"""
RAG Engine — Vector Store interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional
from app.rag.filters import MetadataFilters


class BaseVectorStore(ABC):
    """
    Decoupled interface representing vector storage engines.
    """

    @abstractmethod
    async def create_index(self, kb_id: int, dimensions: int) -> None:
        """Create/rebuild vector indexing tables or fields."""
        pass

    @abstractmethod
    async def upsert(
        self,
        kb_id: int,
        chunk_id: int,
        vector: list[float],
        metadata: dict[str, Any],
    ) -> None:
        """Store a single chunk vector representation."""
        pass

    @abstractmethod
    async def batch_upsert(
        self,
        kb_id: int,
        items: list[tuple[int, list[float], dict[str, Any]]],
    ) -> None:
        """Store multiple chunk vector representations in batch."""
        pass

    @abstractmethod
    async def delete(self, kb_id: int, chunk_id: int) -> None:
        """Delete a vector representation."""
        pass

    @abstractmethod
    async def search(
        self,
        kb_id: int,
        query_vector: list[float],
        top_k: int,
        filters: Optional[MetadataFilters] = None,
    ) -> list[tuple[int, float, dict[str, Any]]]:
        """
        Search vector database. Returns a list of (chunk_id, similarity_score, metadata).
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check vector store health status."""
        pass
