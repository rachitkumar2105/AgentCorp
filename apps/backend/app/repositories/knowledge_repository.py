"""
Knowledge Base repository.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.knowledge_base import KnowledgeBase
from app.repositories.base_repository import BaseRepository


class KnowledgeBaseRepository(BaseRepository[KnowledgeBase]):
    """
    Repository for KnowledgeBase model operations.
    """

    def __init__(self, db: Session):
        super().__init__(KnowledgeBase, db)

    def get_by_org_and_id(self, org_id: int, kb_id: int) -> KnowledgeBase | None:
        """Get a knowledge base by organization and id, excluding soft-deleted ones."""
        stmt = select(KnowledgeBase).where(
            KnowledgeBase.organization_id == org_id,
            KnowledgeBase.id == kb_id,
            KnowledgeBase.is_deleted == False,
        )
        return self.db.scalar(stmt)

    def list_by_org(self, org_id: int) -> list[KnowledgeBase]:
        """List active knowledge bases for an organization."""
        stmt = select(KnowledgeBase).where(
            KnowledgeBase.organization_id == org_id,
            KnowledgeBase.is_deleted == False,
        )
        return list(self.db.scalars(stmt).all())
