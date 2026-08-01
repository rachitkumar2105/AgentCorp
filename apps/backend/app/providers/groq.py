"""
Groq Provider implementation.

Full production implementation with both non-streaming and streaming support.
"""

import json
import logging
import time
from collections.abc import AsyncGenerator
from typing import Any

import groq
from groq import AsyncGroq

from app.config.settings import settings
from app.providers.base import BaseProvider
from app.providers.exceptions import (
    ProviderAuthenticationError,
    ProviderBadRequestError,
    ProviderConnectionError,
    ProviderError,
    ProviderModelNotSupportedError,
    ProviderNotFoundError,
    ProviderRateLimitError,
    ProviderStreamingError,
    ProviderTimeoutError,
)
from app.providers.schemas import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    EmbeddingRequest,
    EmbeddingResponse,
    MessageRole,
    StreamChunk,
    ToolCall,
    Usage,
)

logger = logging.getLogger(__name__)


class GroqProvider(BaseProvider):
    """
    Groq API client wrapper.

    Supports:
      - chat()        : standard blocking completions
      - stream_chat() : token-by-token streaming via async generator
    """

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or settings.GROQ_API_KEY
        if not self.api_key:
            raise ProviderAuthenticationError("Groq API key is missing or not configured.")
        self.client = AsyncGroq(api_key=self.api_key)

    @property
    def supports_tools(self) -> bool:
        return True

    @property
    def supports_streaming(self) -> bool:
        return True

    @property
    def supports_embeddings(self) -> bool:
        return False

    @property
    def supports_images(self) -> bool:
        return False

    @property
    def supports_reasoning(self) -> bool:
        return False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _map_exception(self, exc: Exception) -> Exception:
        """Map groq SDK exceptions to custom provider exceptions."""
        if isinstance(exc, groq.AuthenticationError):
            return ProviderAuthenticationError(str(exc))
        if isinstance(exc, groq.RateLimitError):
            return ProviderRateLimitError(str(exc))
        if isinstance(exc, groq.APITimeoutError):
            return ProviderTimeoutError(str(exc))
        if isinstance(exc, groq.APIConnectionError):
            return ProviderConnectionError(str(exc))
        if isinstance(exc, groq.NotFoundError):
            return ProviderNotFoundError(str(exc))
        if isinstance(exc, groq.BadRequestError):
            return ProviderBadRequestError(str(exc))
        if isinstance(exc, groq.APIError):
            return ProviderError(str(exc))
        return exc

    def _build_messages(self, messages: list[ChatMessage]) -> list[dict[str, Any]]:
        """Convert standard ChatMessage objects into the Groq API message dictionaries."""
        payload = []
        for msg in messages:
            msg_dict: dict[str, Any] = {"role": msg.role.value, "content": msg.content}
            if msg.name:
                msg_dict["name"] = msg.name
            if msg.tool_call_id:
                msg_dict["tool_call_id"] = msg.tool_call_id
            payload.append(msg_dict)
        return payload

    def _build_tools(self, tools: list[Any]) -> list[dict[str, Any]] | None:
        """Convert standard ToolDefinition objects into the Groq API tools configuration."""
        if not tools:
            return None

        tools_payload = []
        for tool in tools:
            properties: dict[str, dict[str, Any]] = {}
            for param_name, param in tool.parameters.items():
                properties[param_name] = {"type": param.type}
                if param.description:
                    properties[param_name]["description"] = param.description
                if param.enum:
                    properties[param_name]["enum"] = param.enum

            tools_payload.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": tool.required,
                    },
                },
            })
        return tools_payload

    def _build_kwargs(self, request: ChatRequest) -> dict[str, Any]:
        """Build keyword arguments for the Groq completions API call."""
        messages = self._build_messages(request.messages)
        tools = self._build_tools(request.tools)

        kwargs: dict[str, Any] = {
            "model": request.model,
            "messages": messages,
            "temperature": request.temperature,
        }
        if request.max_tokens:
            kwargs["max_tokens"] = request.max_tokens
        if request.top_p is not None:
            kwargs["top_p"] = request.top_p
        if tools:
            kwargs["tools"] = tools
            if request.tool_choice:
                kwargs["tool_choice"] = request.tool_choice
        if request.stop:
            kwargs["stop"] = request.stop
        return kwargs

    def _parse_response(self, response: Any) -> ChatResponse:
        """Parse native Groq API response into a standard ChatResponse."""
        choice = response.choices[0]

        tool_calls = []
        if choice.message.tool_calls:
            for tc in choice.message.tool_calls:
                try:
                    args = json.loads(tc.function.arguments) if tc.function.arguments else {}
                except json.JSONDecodeError:
                    args = {}
                tool_calls.append(ToolCall(
                    id=tc.id,
                    name=tc.function.name,
                    arguments=args,
                ))

        usage = None
        if response.usage:
            usage = Usage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
            )

        return ChatResponse(
            model=response.model,
            message=ChatMessage(
                role=MessageRole(choice.message.role),
                content=choice.message.content or "",
            ),
            finish_reason=choice.finish_reason,
            usage=usage,
            tool_calls=tool_calls,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def chat(self, request: ChatRequest) -> ChatResponse:
        """
        Generate chat completion using Groq (non-streaming).
        """
        logger.info(f"GroqProvider: Executing chat request with model {request.model}")
        start_time = time.perf_counter()
        try:
            kwargs = self._build_kwargs(request)
            kwargs["stream"] = False

            response = await self.client.chat.completions.create(**kwargs)

            latency = time.perf_counter() - start_time
            logger.info(f"GroqProvider: Chat completion succeeded in {latency:.4f}s")

            return self._parse_response(response)

        except Exception as exc:
            latency = time.perf_counter() - start_time
            mapped_exc = self._map_exception(exc)
            logger.error(
                f"GroqProvider: Chat completion failed after {latency:.4f}s: {mapped_exc}",
                exc_info=True,
            )
            raise mapped_exc from exc

    async def stream_chat(
        self,
        request: ChatRequest,
    ) -> AsyncGenerator[StreamChunk, None]:
        """
        Stream chat completion tokens from Groq as an async generator.

        Yields one StreamChunk per delta received from the Groq streaming API.
        The final chunk carries ``finish_reason`` and ``usage`` (when available).

        On any error the generator raises ``ProviderStreamingError`` rather than
        yielding a partial response, so the caller can emit a clean SSE error event.
        """
        logger.info(f"GroqProvider: Starting stream_chat with model {request.model}")
        start_time = time.perf_counter()
        index = 0

        try:
            kwargs = self._build_kwargs(request)
            # Force streaming — ignore any stream=False set on the request
            kwargs["stream"] = True
            # stream_options exposes usage on the final chunk (Groq supports this)
            kwargs["stream_options"] = {"include_usage": True}

            stream = await self.client.chat.completions.create(**kwargs)

            async for chunk in stream:
                if not chunk.choices:
                    # Final chunk carries only usage; no choices
                    usage: Usage | None = None
                    if hasattr(chunk, "usage") and chunk.usage:
                        usage = Usage(
                            prompt_tokens=chunk.usage.prompt_tokens,
                            completion_tokens=chunk.usage.completion_tokens,
                            total_tokens=chunk.usage.total_tokens,
                        )
                    yield StreamChunk(
                        token="",
                        index=index,
                        finish_reason="stop",
                        usage=usage,
                        model=request.model,
                    )
                    break

                choice = chunk.choices[0]
                delta = choice.delta
                token_text = delta.content or ""
                finish_reason: str | None = choice.finish_reason

                # Build usage only on final chunk
                usage = None
                if finish_reason and hasattr(chunk, "usage") and chunk.usage:
                    usage = Usage(
                        prompt_tokens=chunk.usage.prompt_tokens,
                        completion_tokens=chunk.usage.completion_tokens,
                        total_tokens=chunk.usage.total_tokens,
                    )

                yield StreamChunk(
                    token=token_text,
                    index=index,
                    finish_reason=finish_reason,
                    usage=usage,
                    model=chunk.model or request.model,
                )
                index += 1

                # Stop iterating after the final chunk
                if finish_reason:
                    break

            latency = time.perf_counter() - start_time
            logger.info(
                f"GroqProvider: Stream completed — {index} chunks in {latency:.4f}s"
            )

        except Exception as exc:
            latency = time.perf_counter() - start_time
            mapped_exc = self._map_exception(exc)
            logger.error(
                f"GroqProvider: Stream failed after {latency:.4f}s and {index} chunks: {mapped_exc}",
                exc_info=True,
            )
            raise ProviderStreamingError(str(mapped_exc)) from exc

    async def embeddings(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """
        Embeddings are not supported natively by Groq.
        """
        raise ProviderModelNotSupportedError("Groq does not support text embeddings.")

    async def health_check(self) -> bool:
        """
        Verify credentials and connection status by executing a simple check.
        """
        try:
            await self.list_models()
            return True
        except Exception as exc:
            logger.warning(f"Groq health check failed: {exc}")
            return False

    async def list_models(self) -> list[str]:
        """
        List all models supported by this provider.
        """
        try:
            response = await self.client.models.list()
            return [m.id for m in response.data]
        except Exception as exc:
            raise self._map_exception(exc) from exc

    async def close(self) -> None:
        """
        Close underlying client connections.
        """
        await self.client.close()
