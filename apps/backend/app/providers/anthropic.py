"""
Anthropic Provider placeholder implementation.

stream_chat() raises ProviderModelNotSupportedError until the full implementation
is added in a future prompt.
"""

from collections.abc import AsyncGenerator

from app.providers.base import BaseProvider
from app.providers.exceptions import ProviderModelNotSupportedError
from app.providers.schemas import (
    ChatRequest,
    ChatResponse,
    EmbeddingRequest,
    EmbeddingResponse,
    StreamChunk,
)


class AnthropicProvider(BaseProvider):
    """
    Anthropic API client wrapper (Placeholder).
    """

    def __init__(self, api_key: str | None = None) -> None:
        pass

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
        return True

    @property
    def supports_reasoning(self) -> bool:
        return True

    async def chat(self, request: ChatRequest) -> ChatResponse:
        raise ProviderModelNotSupportedError("Anthropic provider is not yet implemented.")

    async def stream_chat(
        self,
        request: ChatRequest,
    ) -> AsyncGenerator[StreamChunk, None]:
        """Streaming is not yet implemented for Anthropic."""
        raise ProviderModelNotSupportedError("Anthropic streaming is not yet implemented.")
        yield  # satisfies AsyncGenerator protocol

    async def embeddings(self, request: EmbeddingRequest) -> EmbeddingResponse:
        raise ProviderModelNotSupportedError("Anthropic provider is not yet implemented.")

    async def health_check(self) -> bool:
        return False

    async def list_models(self) -> list[str]:
        return []

    async def close(self) -> None:
        pass
