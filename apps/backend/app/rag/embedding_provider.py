"""
RAG Engine — Embedding Provider interfaces.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional
from app.rag.exceptions import EmbeddingGenerationError


class BaseEmbeddingProvider(ABC):
    """
    Interface for vector embedding providers.
    """

    @abstractmethod
    async def generate_embedding(self, text: str, model: str) -> list[float]:
        """Generate a single vector embedding."""
        pass

    @abstractmethod
    async def generate_embeddings(self, texts: list[str], model: str) -> list[list[float]]:
        """Generate a batch of vector embeddings."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check provider connection status."""
        pass


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """
    OpenAI embeddings provider (stub).
    """

    async def generate_embedding(self, text: str, model: str) -> list[float]:
        # Return a mocked 1536-dimensional float vector
        return [0.1] * 1536

    async def generate_embeddings(self, texts: list[str], model: str) -> list[list[float]]:
        return [[0.1] * 1536 for _ in texts]

    async def health_check(self) -> bool:
        return True


class GeminiEmbeddingProvider(BaseEmbeddingProvider):
    """
    Gemini embeddings provider (stub).
    """

    async def generate_embedding(self, text: str, model: str) -> list[float]:
        return [0.2] * 768

    async def generate_embeddings(self, texts: list[str], model: str) -> list[list[float]]:
        return [[0.2] * 768 for _ in texts]

    async def health_check(self) -> bool:
        return True


class OllamaEmbeddingProvider(BaseEmbeddingProvider):
    """
    Ollama local embeddings provider (stub).
    """

    async def generate_embedding(self, text: str, model: str) -> list[float]:
        return [0.3] * 4096

    async def generate_embeddings(self, texts: list[str], model: str) -> list[list[float]]:
        return [[0.3] * 4096 for _ in texts]

    async def health_check(self) -> bool:
        return True
