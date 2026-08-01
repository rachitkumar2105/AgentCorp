"""
RAG Engine — Retriever.
"""

from __future__ import annotations

from typing import Optional
from sqlalchemy.orm import Session

from app.rag.embedding_provider import OpenAIEmbeddingProvider
from app.rag.filters import MetadataFilters
from app.rag.vector_store_factory import VectorStoreFactory


class Retriever:
    """
    Fetches raw matched vectors.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.embedding_provider = OpenAIEmbeddingProvider()
        self.vector_store = VectorStoreFactory.get_vector_store(db)

    async def retrieve_candidates(
        self,
        kb_id: int,
        query: str,
        top_k: int,
        filters: Optional[MetadataFilters] = None,
        embedding_model: str = "text-embedding-3-small",
    ) -> list[tuple[int, float, dict]]:
        """
        Embeds queries and queries vector database backends.
        """
        vector = await self.embedding_provider.generate_embedding(query, embedding_model)
        return await self.vector_store.search(
            kb_id=kb_id,
            query_vector=vector,
            top_k=top_k,
            filters=filters,
        )
