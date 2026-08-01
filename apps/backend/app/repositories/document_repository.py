"""
Knowledge Document Repository.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.knowledge_document import KnowledgeDocument
from app.repositories.base_repository import BaseRepository


class DocumentRepository(BaseRepository[KnowledgeDocument]):
    """
    Repository for KnowledgeDocument model operations.
    """

    def __init__(self, db: Session):
        super().__init__(KnowledgeDocument, db)

    def get_by_checksum_in_kb(self, checksum: str, kb_id: int) -> KnowledgeDocument | None:
        """Find a active document by checksum inside a specific knowledge base."""
        stmt = select(KnowledgeDocument).where(
            KnowledgeDocument.knowledge_base_id == kb_id,
            KnowledgeDocument.checksum == checksum,
            KnowledgeDocument.is_deleted == False,
        )
        return self.db.scalar(stmt)

    def list_by_kb(self, kb_id: int) -> list[KnowledgeDocument]:
        """List active documents in a knowledge base."""
        stmt = select(KnowledgeDocument).where(
            KnowledgeDocument.knowledge_base_id == kb_id,
            KnowledgeDocument.is_deleted == False,
        )
        return list(self.db.scalars(stmt).all())

    def get_active(self, doc_id: int) -> KnowledgeDocument | None:
        """Retrieve a document if it is active and not soft-deleted."""
        stmt = select(KnowledgeDocument).where(
            KnowledgeDocument.id == doc_id,
            KnowledgeDocument.is_deleted == False,
        )
        return self.db.scalar(stmt)
