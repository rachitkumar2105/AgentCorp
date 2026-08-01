"""
RAG Engine — Embedding Service.

Coordinates caching, generation, and storage pipeline logic.
"""

from __future__ import annotations

import logging
from sqlalchemy.orm import Session

from app.models.knowledge_document import KnowledgeDocument
from app.models.knowledge_chunk import KnowledgeChunk
from app.rag.embedding_provider import (
    BaseEmbeddingProvider,
    OpenAIEmbeddingProvider,
    GeminiEmbeddingProvider,
    OllamaEmbeddingProvider,
)
from app.rag.vector_store_factory import VectorStoreFactory

logger = logging.getLogger("embedding_service")


class EmbeddingService:
    """
    Manages vector creation and sync loops for chunks.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.openai_provider = OpenAIEmbeddingProvider()
        self.gemini_provider = GeminiEmbeddingProvider()
        self.ollama_provider = OllamaEmbeddingProvider()
        self.vector_store = VectorStoreFactory.get_vector_store(db)

    def _resolve_provider(self, provider_name: str) -> BaseEmbeddingProvider:
        name = provider_name.lower()
        if name == "openai":
            return self.openai_provider
        elif name == "gemini":
            return self.gemini_provider
        elif name == "ollama":
            return self.ollama_provider
        return self.openai_provider

    async def generate_and_store_document_embeddings(
        self,
        doc: KnowledgeDocument,
        provider_name: str = "openai",
        model: str = "text-embedding-3-small",
        dimensions: int = 1536,
    ) -> None:
        """
        Runs the processing pipeline logic for chunk vectors:
          1. Retrieve active document chunks
          2. Check embedding cache state
          3. Generate using resolved embedding provider
          4. Write into Vector Store
        """
        provider = self._resolve_provider(provider_name)
        chunks = [c for c in doc.chunks if c.embedding_status != "READY"]
        if not chunks:
            logger.info("All chunks for document %d already embedded.", doc.id)
            return

        texts = [chunk.text for chunk in chunks]
        # Generate embeddings
        vectors = await provider.generate_embeddings(texts, model)

        # Build index table for KB
        await self.vector_store.create_index(doc.knowledge_base_id, dimensions)

        upsert_items = []
        for idx, chunk in enumerate(chunks):
            vector = vectors[idx]
            metadata = {
                "document_id": doc.id,
                "knowledge_base_id": doc.knowledge_base_id,
                "language": doc.language or "en",
            }
            upsert_items.append((chunk.id, vector, metadata))
            chunk.embedding_status = "READY"

        await self.vector_store.batch_upsert(doc.knowledge_base_id, upsert_items)
        self.db.commit()
        logger.info("Successfully built and stored %d embeddings for doc %d", len(chunks), doc.id)
