"""
Abstract base class for all AI providers.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Any, Self

from app.providers.schemas import ChatRequest, ChatResponse, EmbeddingRequest, EmbeddingResponse, StreamChunk


class BaseProvider(ABC):
    """
    Interface that all concrete providers must implement.
    """

    @property
    @abstractmethod
    def supports_tools(self) -> bool:
        """Indicate if the provider supports tool calling."""
        pass

    @property
    @abstractmethod
    def supports_streaming(self) -> bool:
        """Indicate if the provider supports response streaming."""
        pass

    @property
    @abstractmethod
    def supports_embeddings(self) -> bool:
        """Indicate if the provider supports generating vector embeddings."""
        pass

    @property
    @abstractmethod
    def supports_images(self) -> bool:
        """Indicate if the provider supports multi-modal image inputs."""
        pass

    @property
    @abstractmethod
    def supports_reasoning(self) -> bool:
        """Indicate if the provider supports advanced reasoning paths."""
        pass

    @abstractmethod
    async def chat(self, request: ChatRequest) -> ChatResponse:
        """
        Generate a text response based on the chat request.
        """
        pass

    @abstractmethod
    async def stream_chat(
        self,
        request: ChatRequest,
    ) -> AsyncGenerator[StreamChunk, None]:
        """
        Stream chat completion tokens as an async generator.

        Yields StreamChunk objects one at a time in the order received from
        the provider.  The final chunk carries ``finish_reason`` and optionally
        ``usage``.

        Providers that do not yet support streaming must raise
        ``ProviderModelNotSupportedError`` from this method.  They must NOT
        return an empty generator, as that would silently produce an empty
        response.
        """
        # This pragma makes mypy happy for abstract async generators
        raise NotImplementedError
        yield  # noqa: unreachable — satisfies AsyncGenerator protocol

    @abstractmethod
    async def embeddings(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """
        Generate embeddings for the given input request.
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the provider service is healthy and accessible.
        """
        pass

    @abstractmethod
    async def list_models(self) -> list[str]:
        """
        List all models supported by this provider.
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """
        Close any underlying resources or connections.
        """
        pass

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type: type | None, exc_val: BaseException | None, exc_tb: Any | None) -> None:
        await self.close()
