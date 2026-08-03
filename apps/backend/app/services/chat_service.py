"""
Chat Service — core business logic for the Chat Engine.

Responsibilities:
  - Validate conversations, organisations, agents, and permissions
  - Persist user and assistant messages
  - Delegate AI execution exclusively to ProviderService (acting as the
    AI Orchestrator layer in this codebase)
  - Return normalised ChatResponseSchema objects

This service NEVER:
  - Calls a provider directly
  - Builds prompts (delegated to PromptBuilder)
  - Manages context windows (delegated to ContextBuilder)
  - Exposes provider-specific details to the API layer
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import Optional

from fastapi import HTTPException, status

from app.models.agent import Agent
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user import User
from app.providers.schemas import ChatMessage, ChatRequest, MessageRole, ToolDefinition, ToolParameter, Usage
from app.repositories.agent_repository import AgentRepository
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository
from app.schemas.chat import (
    AssistantMessageSchema,
    ChatCreateRequest,
    ChatContinueRequest,
    ChatRegenerateRequest,
    ChatResponseSchema,
    ChatRetryRequest,
    ConversationDetailSchema,
    MessageSchema,
    UsageSchema,
)
from app.services.context_builder import ContextBuilder
from app.services.knowledge_service import KnowledgeService
from app.services.memory_service import MemoryService
from app.services.prompt_builder import PromptBuilder
from app.services.provider_service import ProviderService
from app.services.rag_service import RAGService
from app.services.tool_execution_service import ToolExecutionService
from app.schemas.tool_execution import ToolCallRequest, ToolMetadata

logger = logging.getLogger("chat_service")


class ChatService:
    """
    Chat Engine business logic service.

    Injected with all required repositories and the ProviderService which
    acts as the AI Orchestration layer.  Never instantiated directly inside
    endpoint handlers; always obtained via ``get_chat_service()``.
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
    # Public interface
    # ------------------------------------------------------------------

    def create_chat(
        self,
        payload: ChatCreateRequest,
        current_user: User,
        organization_id: int,
    ) -> ChatResponseSchema:
        """
        Create a new conversation and return the first assistant message.

        Flow:
          1. Validate agent (exists, active, belongs to org)
          2. Create conversation row
          3. Persist user message
          4. Execute AI via ProviderService
          5. Persist assistant message
          6. Return ChatResponseSchema
        """
        request_id = _new_request_id()
        logger.info(
            "create_chat | request_id=%s org_id=%s user_id=%s agent_id=%s",
            request_id,
            organization_id,
            current_user.id,
            payload.agent_id,
        )

        agent = self._validate_agent(payload.agent_id, organization_id)

        # Create conversation
        conversation = Conversation(
            organization_id=organization_id,
            agent_id=agent.id,
            user_id=current_user.id,
            title=payload.message[:100],  # sensible default title
            runtime_version=payload.runtime_version,
        )
        conversation = self._conversations.create(conversation)

        return self._execute_and_persist(
            request_id=request_id,
            conversation=conversation,
            agent=agent,
            user_message=payload.message,
            provider_override=payload.provider,
            model_override=payload.model,
            temperature=payload.temperature,
            top_p=payload.top_p,
            max_tokens=payload.max_tokens,
        )

    def continue_chat(
        self,
        conversation_id: int,
        payload: ChatContinueRequest,
        current_user: User,
        organization_id: int,
    ) -> ChatResponseSchema:
        """
        Continue an existing conversation with a new user message.

        Flow:
          1. Load and validate conversation
          2. Validate agent
          3. Persist user message
          4. Execute AI via ProviderService
          5. Persist assistant message
          6. Return ChatResponseSchema
        """
        request_id = _new_request_id()
        logger.info(
            "continue_chat | request_id=%s org_id=%s conv_id=%s user_id=%s",
            request_id,
            organization_id,
            conversation_id,
            current_user.id,
        )

        conversation = self._validate_conversation(conversation_id, organization_id, current_user)
        agent = self._validate_agent(conversation.agent_id, organization_id)

        return self._execute_and_persist(
            request_id=request_id,
            conversation=conversation,
            agent=agent,
            user_message=payload.message,
            provider_override=payload.provider,
            model_override=payload.model,
            temperature=payload.temperature,
            top_p=payload.top_p,
            max_tokens=payload.max_tokens,
        )

    def regenerate_response(
        self,
        conversation_id: int,
        payload: ChatRegenerateRequest,
        current_user: User,
        organization_id: int,
    ) -> ChatResponseSchema:
        """
        Generate a NEW assistant message for the existing conversation.

        History is preserved intact; no messages are deleted.  Compatible
        with future conversation-branching implementations.

        Flow:
          1. Load and validate conversation
          2. Retrieve the last user message to reconstruct the prompt
          3. Execute AI via ProviderService
          4. Persist a new assistant message
          5. Return ChatResponseSchema
        """
        request_id = _new_request_id()
        logger.info(
            "regenerate_response | request_id=%s org_id=%s conv_id=%s",
            request_id,
            organization_id,
            conversation_id,
        )

        conversation = self._validate_conversation(conversation_id, organization_id, current_user)
        agent = self._validate_agent(conversation.agent_id, organization_id)

        last_user_msg = self._messages.get_last_user_message(conversation_id)
        if last_user_msg is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No user message found in this conversation to regenerate a response for.",
            )

        return self._execute_and_persist(
            request_id=request_id,
            conversation=conversation,
            agent=agent,
            user_message=last_user_msg.content,
            provider_override=payload.provider,
            model_override=payload.model,
            temperature=payload.temperature,
            top_p=payload.top_p,
            max_tokens=payload.max_tokens,
            persist_user_message=False,  # do NOT re-add the user message
        )

    def retry_failed_message(
        self,
        conversation_id: int,
        payload: ChatRetryRequest,
        current_user: User,
        organization_id: int,
    ) -> ChatResponseSchema:
        """
        Retry the AI Orchestrator for the last assistant message.

        Intended for cases where provider execution failed (network errors,
        rate limits, etc.).  No duplicate user messages are created.

        Flow:
          1. Load and validate conversation
          2. Retrieve the last user message for context reconstruction
          3. Execute AI via ProviderService
          4. Persist a new assistant message
          5. Return ChatResponseSchema
        """
        request_id = _new_request_id()
        logger.info(
            "retry_failed_message | request_id=%s org_id=%s conv_id=%s",
            request_id,
            organization_id,
            conversation_id,
        )

        conversation = self._validate_conversation(conversation_id, organization_id, current_user)
        agent = self._validate_agent(conversation.agent_id, organization_id)

        last_user_msg = self._messages.get_last_user_message(conversation_id)
        if last_user_msg is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No user message found in this conversation to retry.",
            )

        return self._execute_and_persist(
            request_id=request_id,
            conversation=conversation,
            agent=agent,
            user_message=last_user_msg.content,
            provider_override=payload.provider,
            model_override=payload.model,
            persist_user_message=False,
        )

    def get_conversation(
        self,
        conversation_id: int,
        current_user: User,
        organization_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> ConversationDetailSchema:
        """
        Return conversation metadata plus a paginated message history.

        Future-ready: pagination parameters are already part of the schema
        and will continue to work as message volume grows.
        """
        offset = (page - 1) * page_size

        conversation, messages, total = self._conversations.get_with_messages(
            conversation_id=conversation_id,
            organization_id=organization_id,
            offset=offset,
            limit=page_size,
        )

        if conversation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found.",
            )

        # Ownership check: the user must own the conversation (or be superuser)
        if not current_user.is_superuser and conversation.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this conversation.",
            )

        return ConversationDetailSchema(
            conversation_id=conversation.id,
            title=conversation.title,
            runtime_version=getattr(conversation, "runtime_version", None),
            agent_id=conversation.agent_id,
            organization_id=conversation.organization_id,
            user_id=conversation.user_id,
            messages=[_message_to_schema(m) for m in messages],
            page=page,
            page_size=page_size,
            total_messages=total,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _validate_conversation(
        self,
        conversation_id: int,
        organization_id: int,
        current_user: User,
    ) -> Conversation:
        """
        Load a conversation and enforce organisation + ownership isolation.

        Raises 404 if not found, 403 if the user does not own it.
        """
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

    def _validate_agent(
        self,
        agent_id: int,
        organization_id: int,
    ) -> Agent:
        """
        Load an agent and verify it is active and belongs to the organisation.

        Raises 404 if missing, 403 if wrong org, 422 if inactive.
        """
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

    def _execute_and_persist(
        self,
        *,
        request_id: str,
        conversation: Conversation,
        agent: Agent,
        user_message: str,
        provider_override: Optional[str],
        model_override: Optional[str],
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        persist_user_message: bool = True,
    ) -> ChatResponseSchema:
        """
        Core execution pipeline shared by all POST endpoints.

        1. Optionally persist the user message
        2. Build context from conversation history
        3. Build the full prompt (system + history + new message)
        4. Invoke ProviderService (AI Orchestrator)
        5. Persist the assistant message with full metadata
        6. Return a normalised ChatResponseSchema

        Args:
            persist_user_message: Set to False for regenerate / retry to
                avoid duplicating the user turn in the history.
        """
        # 1. Snapshot history BEFORE the new user message is added
        #    This ensures the current user turn is not duplicated in context.
        history_before = self._messages.get_by_conversation(conversation.id)
        context = self._context_builder.build_context(history_before)
        runtime_context = self._build_runtime_context(
            organization_id=conversation.organization_id,
            agent_id=agent.id,
            user_message=user_message,
        )

        # 2. Persist user message (skipped for regenerate/retry)
        if persist_user_message:
            self._messages.create_user_message(
                conversation_id=conversation.id,
                content=user_message,
            )

        # 3. Build full prompt (system + history snapshot + current user message)
        prompt_messages = self._prompt_builder.build_prompt(
            system_prompt=agent.system_prompt,
            history=context,
            new_user_message=user_message,
            memory_context=runtime_context["memory_context"],
            knowledge_context=runtime_context["knowledge_context"],
            tool_context=runtime_context["tool_context"],
        )

        # 4. Resolve model
        resolved_model = model_override or agent.model_name
        resolved_temperature = temperature if temperature is not None else agent.temperature
        resolved_max_tokens = max_tokens or agent.max_tokens

        chat_request = ChatRequest(
            model=resolved_model,
            messages=prompt_messages,
            temperature=resolved_temperature,
            max_tokens=resolved_max_tokens,
            top_p=top_p,
            tools=runtime_context["tools"],
        )

        # 5. Execute via ProviderService (the AI Orchestrator)
        #    ProviderService.chat() is async; we bridge it into the sync
        #    service context by running it in a dedicated thread so that
        #    we never interfere with FastAPI's own event loop.
        start_ts = time.perf_counter()
        try:
            import asyncio
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(
                    asyncio.run,
                    self._provider_service.chat(
                        chat_request,
                        provider_name=provider_override,
                    ),
                )
                ai_response = future.result()
        except Exception as exc:
            latency = time.perf_counter() - start_ts
            logger.error(
                "AI execution failed | request_id=%s conv_id=%s org_id=%s provider=%s latency=%.4fs error=%s",
                request_id,
                conversation.id,
                conversation.organization_id,
                provider_override or "auto",
                latency,
                exc,
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"AI provider execution failed: {exc}",
            ) from exc

        if ai_response.tool_calls and self._tool_execution_service is not None:
            ai_response = self._execute_tool_loop(
                initial_request=chat_request,
                initial_response=ai_response,
                current_user_id=conversation.user_id,
                organization_id=conversation.organization_id,
                agent_id=agent.id,
                conversation_id=conversation.id,
                provider_override=provider_override,
            )

        latency = time.perf_counter() - start_ts

        # 6. Extract metadata
        usage = ai_response.usage
        provider_used = ai_response.model.split("/")[0] if "/" in ai_response.model else (provider_override or "unknown")
        model_used = ai_response.model
        finish_reason = ai_response.finish_reason or "stop"
        assistant_content = ai_response.message.content

        prompt_tokens = usage.prompt_tokens if usage else 0
        completion_tokens = usage.completion_tokens if usage else 0
        total_tokens = usage.total_tokens if usage else 0

        logger.info(
            "AI execution success | request_id=%s conv_id=%s org_id=%s provider=%s model=%s "
            "latency=%.4fs prompt_tokens=%d completion_tokens=%d total_tokens=%d",
            request_id,
            conversation.id,
            conversation.organization_id,
            provider_used,
            model_used,
            latency,
            prompt_tokens,
            completion_tokens,
            total_tokens,
        )

        # 7. Persist assistant message
        assistant_msg = self._messages.create_assistant_message(
            conversation_id=conversation.id,
            content=assistant_content,
            provider=provider_used,
            model_used=model_used,
            finish_reason=finish_reason,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        )

        # 8. Build and return response
        return ChatResponseSchema(
            conversation_id=conversation.id,
            runtime_version=getattr(conversation, "runtime_version", None),
            assistant_message=AssistantMessageSchema(
                id=assistant_msg.id,
                role="assistant",
                content=assistant_content,
                provider=provider_used,
                model_used=model_used,
                finish_reason=finish_reason,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                created_at=assistant_msg.created_at,
            ),
            provider=provider_used,
            model=model_used,
            usage=UsageSchema(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
            ),
            finish_reason=finish_reason,
            created_at=assistant_msg.created_at,
        )

    def _build_runtime_context(
        self,
        *,
        organization_id: int,
        agent_id: int,
        user_message: str,
    ) -> dict:
        memory_context = self._retrieve_memory_context(
            organization_id=organization_id,
            agent_id=agent_id,
            query=user_message,
        )
        knowledge_context = self._retrieve_knowledge_context(
            organization_id=organization_id,
            query=user_message,
        )
        tool_metadata = self._discover_tool_metadata(
            agent_id=agent_id,
            organization_id=organization_id,
        )

        return {
            "memory_context": memory_context,
            "knowledge_context": knowledge_context,
            "tool_context": self._format_tool_context(tool_metadata),
            "tools": self._to_provider_tool_definitions(tool_metadata),
        }

    def _retrieve_memory_context(self, *, organization_id: int, agent_id: int, query: str) -> str | None:
        if self._memory_service is None:
            return None
        try:
            memories = _run_async(
                self._memory_service.retrieve_memories(
                    org_id=organization_id,
                    agent_id=agent_id,
                    query=query,
                    top_k=5,
                )
            )
        except Exception as exc:
            logger.warning("memory retrieval skipped | org_id=%s agent_id=%s error=%s", organization_id, agent_id, exc)
            return None
        if not memories:
            return None
        return "\n".join(f"- {m.title}: {m.content}" if m.title else f"- {m.content}" for m in memories)

    def _retrieve_knowledge_context(self, *, organization_id: int, query: str) -> str | None:
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
                context = _run_async(
                    self._rag_service.retrieve_context(
                        kb_id=kb.id,
                        query=query,
                        top_k=5,
                        max_tokens=2000,
                    )
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

    def _execute_tool_loop(
        self,
        *,
        initial_request: ChatRequest,
        initial_response,
        current_user_id: int,
        organization_id: int,
        agent_id: int,
        conversation_id: int,
        provider_override: str | None,
    ):
        if self._tool_execution_service is None:
            return initial_response

        tool_requests = [
            ToolCallRequest(
                call_id=tool_call.id,
                tool_name=tool_call.name,
                arguments=tool_call.arguments,
            )
            for tool_call in initial_response.tool_calls
        ]
        if not tool_requests:
            return initial_response

        tool_result = _run_async(
            self._tool_execution_service.execute_batch(
                requests=tool_requests,
                current_user=_ServiceUserProxy(id=current_user_id),
                organization_id=organization_id,
                agent_id=agent_id,
                conversation_id=conversation_id,
            )
        )

        followup_messages = list(initial_request.messages)
        if initial_response.message.content:
            followup_messages.append(initial_response.message)
        for result in tool_result.results:
            followup_messages.append(ChatMessage(
                role=MessageRole.TOOL,
                content=result.content,
                name=result.tool_name,
                tool_call_id=result.call_id,
            ))

        followup_request = initial_request.model_copy(update={"messages": followup_messages})
        return _run_async(
            self._provider_service.chat(
                followup_request,
                provider_name=provider_override,
            )
        )

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


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


def _new_request_id() -> str:
    """Generate a unique request correlation ID."""
    return str(uuid.uuid4())


def _run_async(coro):
    import asyncio
    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coro).result()


class _ServiceUserProxy:
    def __init__(self, id: int | None = None) -> None:
        self.id = id
        self.is_superuser = True


def _message_to_schema(message: Message) -> MessageSchema:
    """Convert a Message ORM row to its Pydantic schema."""
    return MessageSchema(
        id=message.id,
        role=message.role,
        content=message.content,
        provider=getattr(message, "provider", None),
        model_used=getattr(message, "model_used", None),
        finish_reason=getattr(message, "finish_reason", None),
        prompt_tokens=getattr(message, "prompt_tokens", None),
        completion_tokens=getattr(message, "completion_tokens", None),
        total_tokens=getattr(message, "total_tokens", None),
        created_at=message.created_at,
    )
