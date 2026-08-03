"""
Streaming Service — core business logic for the Streaming Engine.

Responsibilities:
  - Validate conversation, agent, organisation, and RBAC (same as ChatService)
  - Build context and prompt (via ContextBuilder / PromptBuilder — no duplication)
  - Invoke ProviderService.stream_chat() — never a provider directly
  - Yield SSE-formatted strings token-by-token
  - Persist the final complete assistant message ONLY after stream completion
  - Handle disconnects and cancellations — never persist partial messages
  - Update global stream metrics

WebSocket readiness:
  The core execution method ``stream_response`` is an async generator that
  yields SSE-formatted strings.  A future WebSocket transport can call the
  same method and wrap the output in WebSocket frames instead of an HTTP body.

Architecture invariants:
  - NEVER calls a provider directly
  - NEVER duplicates prompt/context logic from ChatService
  - NEVER persists partial messages
  - NEVER switches providers mid-stream
"""

from __future__ import annotations

import logging
import time
from collections.abc import AsyncGenerator
from typing import Optional

from fastapi import HTTPException, status

from app.models.agent import Agent
from app.models.conversation import Conversation
from app.models.user import User
from app.providers.schemas import ChatRequest, ToolDefinition, ToolParameter
from app.repositories.agent_repository import AgentRepository
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository
from app.schemas.streaming import (
    StreamingChatRequest,
    StreamingCompleted,
    StreamingUsage,
)
from app.services.context_builder import ContextBuilder
from app.services.knowledge_service import KnowledgeService
from app.services.memory_service import MemoryService
from app.services.prompt_builder import PromptBuilder
from app.services.provider_service import ProviderService
from app.services.rag_service import RAGService
from app.services.tool_execution_service import ToolExecutionService
from app.schemas.tool_execution import ToolMetadata
from app.utils.stream_events import (
    StreamMetrics,
    decrement_active,
    format_done_event,
    format_error_event,
    format_token_event,
    increment_active,
    record_cancelled,
    record_completed,
    record_failed,
)

logger = logging.getLogger("streaming_service")


class StreamingService:
    """
    Streaming Engine business logic service.

    Injected with the same collaborators as ChatService so that context
    building, prompt building, and repository access are shared, not
    duplicated.

    Never instantiate directly — obtain via ``get_streaming_service()``.
    """

    def __init__(
        self,
        conversation_repo: ConversationRepository,
        message_repo: MessageRepository,
        agent_repo: AgentRepository,
        provider_service: ProviderService,
        context_builder: ContextBuilder,
        prompt_builder: PromptBuilder,
        memory_service: MemoryService | None = None,
        knowledge_service: KnowledgeService | None = None,
        rag_service: RAGService | None = None,
        tool_execution_service: ToolExecutionService | None = None,
    ) -> None:
        self._conversations = conversation_repo
        self._messages = message_repo
        self._agents = agent_repo
        self._provider_service = provider_service
        self._context_builder = context_builder
        self._prompt_builder = prompt_builder
        self._memory_service = memory_service
        self._knowledge_service = knowledge_service
        self._rag_service = rag_service
        self._tool_execution_service = tool_execution_service

    # ------------------------------------------------------------------
    # Public streaming entry points
    # ------------------------------------------------------------------

    async def stream_new_chat(
        self,
        payload: StreamingChatRequest,
        current_user: User,
        organization_id: int,
    ) -> AsyncGenerator[str, None]:
        """
        Create a new conversation and stream the first assistant response.

        Yields SSE-formatted strings.  The conversation and user message are
        persisted synchronously before the stream starts.  The assistant
        message is persisted only after the stream completes successfully.
        """
        if payload.agent_id is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="agent_id is required when creating a new conversation stream.",
            )

        agent = self._validate_agent(payload.agent_id, organization_id)

        # Create conversation synchronously before yielding any SSE
        conversation = Conversation(
            organization_id=organization_id,
            agent_id=agent.id,
            user_id=current_user.id,
            title=payload.message[:100],
            runtime_version=payload.runtime_version,
        )
        conversation = self._conversations.create(conversation)

        async for event in self._execute_stream(
            payload=payload,
            conversation=conversation,
            agent=agent,
        ):
            yield event

    async def stream_continue_chat(
        self,
        conversation_id: int,
        payload: StreamingChatRequest,
        current_user: User,
        organization_id: int,
    ) -> AsyncGenerator[str, None]:
        """
        Continue an existing conversation as a stream.

        Yields SSE-formatted strings.
        """
        conversation = self._validate_conversation(conversation_id, organization_id, current_user)
        agent = self._validate_agent(conversation.agent_id, organization_id)

        async for event in self._execute_stream(
            payload=payload,
            conversation=conversation,
            agent=agent,
        ):
            yield event

    # ------------------------------------------------------------------
    # Core execution pipeline
    # ------------------------------------------------------------------

    async def _execute_stream(
        self,
        payload: StreamingChatRequest,
        conversation: Conversation,
        agent: Agent,
    ) -> AsyncGenerator[str, None]:
        """
        Core streaming pipeline shared by all entry points.

        Flow:
          1. Snapshot history
          2. Persist user message
          3. Build prompt
          4. Open provider stream
          5. Yield token SSE events
          6. On completion: persist assistant message, yield done event
          7. On cancellation/error: do NOT persist, yield error event

        Implements the WebSocket-ready interface: yields plain strings that
        any transport (SSE body, WebSocket frame) can forward directly.
        """
        metrics = StreamMetrics(
            conversation_id=conversation.id,
            organization_id=conversation.organization_id,
            provider=payload.provider or "auto",
            model=payload.model or agent.model_name,
        )
        increment_active()

        try:
            # ---- 1. Snapshot history before adding the new user message ----
            history_before = self._messages.get_by_conversation(conversation.id)
            context = self._context_builder.build_context(history_before)
            runtime_context = await self._build_runtime_context(
                organization_id=conversation.organization_id,
                agent_id=agent.id,
                user_message=payload.message,
            )

            # ---- 2. Persist user message ----
            self._messages.create_user_message(
                conversation_id=conversation.id,
                content=payload.message,
            )

            # ---- 3. Build prompt ----
            resolved_model = payload.model or agent.model_name
            resolved_temperature = (
                payload.temperature
                if payload.temperature is not None
                else agent.temperature
            )
            resolved_max_tokens = payload.max_tokens or agent.max_tokens

            prompt_messages = self._prompt_builder.build_prompt(
                system_prompt=agent.system_prompt,
                history=context,
                new_user_message=payload.message,
                memory_context=runtime_context["memory_context"],
                knowledge_context=runtime_context["knowledge_context"],
                tool_context=runtime_context["tool_context"],
            )

            chat_request = ChatRequest(
                model=resolved_model,
                messages=prompt_messages,
                temperature=resolved_temperature,
                max_tokens=resolved_max_tokens,
                top_p=payload.top_p,
                stream=True,
                tools=runtime_context["tools"],
            )

            # ---- 4. Open provider stream ----
            collected_tokens: list[str] = []
            finish_reason = "stop"
            final_usage: dict | None = None
            provider_used = payload.provider or "auto"
            model_used = resolved_model

            try:
                async for chunk in self._provider_service.stream_chat(
                    chat_request,
                    provider_name=payload.provider,
                ):
                    # ---- 5. Yield token SSE events ----
                    if chunk.token:
                        collected_tokens.append(chunk.token)
                        metrics.record_token()

                        if chunk.model:
                            model_used = chunk.model
                            provider_used = chunk.model.split("/")[0] if "/" in chunk.model else provider_used

                        yield format_token_event(
                            token=chunk.token,
                            index=chunk.index,
                            provider=provider_used,
                            model=model_used,
                        )

                    if chunk.finish_reason:
                        finish_reason = chunk.finish_reason

                    if chunk.usage:
                        final_usage = {
                            "prompt_tokens": chunk.usage.prompt_tokens,
                            "completion_tokens": chunk.usage.completion_tokens,
                            "total_tokens": chunk.usage.total_tokens,
                        }

            except GeneratorExit:
                # Client disconnected — do not persist
                logger.info(
                    "streaming_service | client disconnected | conv_id=%s org_id=%s",
                    conversation.id,
                    conversation.organization_id,
                )
                metrics.cancelled = True
                record_cancelled()
                decrement_active()
                return

            except Exception as exc:
                logger.error(
                    "streaming_service | provider error | conv_id=%s provider=%s error=%s",
                    conversation.id,
                    provider_used,
                    exc,
                )
                metrics.failed = True
                record_failed()
                decrement_active()
                yield format_error_event(
                    error=str(exc),
                    code="provider_streaming_error",
                )
                return

            # ---- 6. Stream complete — persist assistant message ----
            full_content = "".join(collected_tokens)
            latency = metrics.elapsed()

            assistant_msg = self._messages.create_assistant_message(
                conversation_id=conversation.id,
                content=full_content,
                provider=provider_used,
                model_used=model_used,
                finish_reason=finish_reason,
                prompt_tokens=final_usage.get("prompt_tokens") if final_usage else None,
                completion_tokens=final_usage.get("completion_tokens") if final_usage else None,
                total_tokens=final_usage.get("total_tokens") if final_usage else None,
            )

            metrics.finish_reason = finish_reason
            metrics.completed = True
            record_completed(latency, metrics.tokens_sent)
            decrement_active()

            logger.info(
                "streaming_service | completed | conv_id=%s org_id=%s provider=%s model=%s "
                "latency=%.4fs tokens=%d",
                conversation.id,
                conversation.organization_id,
                provider_used,
                model_used,
                latency,
                metrics.tokens_sent,
            )

            # Yield terminal done event
            yield format_done_event(
                finish_reason=finish_reason,
                usage=final_usage,
                latency=latency,
                tokens_sent=metrics.tokens_sent,
            )

        except HTTPException:
            decrement_active()
            raise

        except Exception as exc:
            logger.error(
                "streaming_service | unexpected error | conv_id=%s error=%s",
                conversation.id,
                exc,
                exc_info=True,
            )
            metrics.failed = True
            record_failed()
            decrement_active()
            yield format_error_event(
                error="An unexpected error occurred during streaming.",
                code="internal_error",
            )

    # ------------------------------------------------------------------
    # Validation helpers (mirror ChatService — no shared base needed)
    # ------------------------------------------------------------------

    async def _build_runtime_context(
        self,
        *,
        organization_id: int,
        agent_id: int,
        user_message: str,
    ) -> dict:
        tool_metadata = self._discover_tool_metadata(
            agent_id=agent_id,
            organization_id=organization_id,
        )
        return {
            "memory_context": await self._retrieve_memory_context(
                organization_id=organization_id,
                agent_id=agent_id,
                query=user_message,
            ),
            "knowledge_context": await self._retrieve_knowledge_context(
                organization_id=organization_id,
                query=user_message,
            ),
            "tool_context": self._format_tool_context(tool_metadata),
            "tools": self._to_provider_tool_definitions(tool_metadata),
        }

    async def _retrieve_memory_context(self, *, organization_id: int, agent_id: int, query: str) -> str | None:
        if self._memory_service is None:
            return None
        try:
            memories = await self._memory_service.retrieve_memories(
                org_id=organization_id,
                agent_id=agent_id,
                query=query,
                top_k=5,
            )
        except Exception as exc:
            logger.warning("memory retrieval skipped | org_id=%s agent_id=%s error=%s", organization_id, agent_id, exc)
            return None
        if not memories:
            return None
        return "\n".join(f"- {m.title}: {m.content}" if m.title else f"- {m.content}" for m in memories)

    async def _retrieve_knowledge_context(self, *, organization_id: int, query: str) -> str | None:
        if self._knowledge_service is None or self._rag_service is None:
            return None
        try:
            knowledge_bases = self._knowledge_service.list_knowledge_bases(organization_id)
        except Exception as exc:
            logger.warning("knowledge base discovery skipped | org_id=%s error=%s", organization_id, exc)
            return None

        contexts: list[str] = []
        for kb in knowledge_bases:
            try:
                context = await self._rag_service.retrieve_context(
                    kb_id=kb.id,
                    query=query,
                    top_k=5,
                    max_tokens=2000,
                )
            except Exception as exc:
                logger.warning("rag retrieval skipped | org_id=%s kb_id=%s error=%s", organization_id, kb.id, exc)
                continue
            if context:
                contexts.append(f"Knowledge base: {kb.name}\n{context}")
        return "\n\n".join(contexts) if contexts else None

    def _discover_tool_metadata(self, *, agent_id: int, organization_id: int) -> list[ToolMetadata]:
        if self._tool_execution_service is None:
            return []
        try:
            return self._tool_execution_service.discover_agent_tools(
                agent_id=agent_id,
                organization_id=organization_id,
                current_user=_ServiceUserProxy(),
            )
        except Exception as exc:
            logger.warning("tool discovery skipped | org_id=%s agent_id=%s error=%s", organization_id, agent_id, exc)
            return []

    def _format_tool_context(self, tool_metadata: list[ToolMetadata]) -> str | None:
        if not tool_metadata:
            return None
        return "\n".join(f"- {tool.name}: {tool.description}" for tool in tool_metadata)

    def _to_provider_tool_definitions(self, tool_metadata: list[ToolMetadata]) -> list[ToolDefinition]:
        definitions: list[ToolDefinition] = []
        for tool in tool_metadata:
            parameters = {
                name: ToolParameter(
                    type=param.type,
                    description=param.description,
                    enum=param.enum,
                )
                for name, param in tool.parameters.properties.items()
            }
            definitions.append(ToolDefinition(
                name=tool.name,
                description=tool.description,
                parameters=parameters,
                required=tool.parameters.required,
            ))
        return definitions

    def _validate_conversation(
        self,
        conversation_id: int,
        organization_id: int,
        current_user: User,
    ) -> Conversation:
        """Load and verify organisation + ownership isolation."""
        conversation = self._conversations.get_by_id_for_org(conversation_id, organization_id)

        if conversation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found.",
            )

        if not current_user.is_superuser and conversation.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this conversation.",
            )

        return conversation

    def _validate_agent(self, agent_id: int, organization_id: int) -> Agent:
        """Load and verify agent is active and belongs to the organisation."""
        agent = self._agents.get(agent_id)

        if agent is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found.",
            )

        if agent.organization_id != organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Agent does not belong to your organisation.",
            )

        if not agent.is_active:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Agent is disabled and cannot process requests.",
            )

        return agent


class _ServiceUserProxy:
    def __init__(self) -> None:
        self.is_superuser = True
