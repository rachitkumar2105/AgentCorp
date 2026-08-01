"""
Knowledge Chunk Repository.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.knowledge_chunk import KnowledgeChunk
from app.repositories.base_repository import BaseRepository


class ChunkRepository(BaseRepository[KnowledgeChunk]):
    """
    Repository for KnowledgeChunk model operations.
    """

    def __init__(self, db: Session):
        super().__init__(KnowledgeChunk, db)

    def list_by_document(self, doc_id: int) -> list[KnowledgeChunk]:
        """List active chunks associated with a document."""
        stmt = select(KnowledgeChunk).where(
            KnowledgeChunk.document_id == doc_id,
            KnowledgeChunk.is_deleted == False,
        )
        return list(self.db.scalars(stmt).all())
