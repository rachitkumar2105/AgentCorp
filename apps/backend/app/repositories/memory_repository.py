"""
Memory Repository.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.memory import Memory
from app.repositories.base_repository import BaseRepository


class MemoryRepository(BaseRepository[Memory]):
    """
    Repository for Memory model database queries.
    """

    def __init__(self, db: Session):
        super().__init__(Memory, db)

    def get_by_org_and_id(self, org_id: int, memory_id: int) -> Memory | None:
        """Fetch memory entry by organization mapping."""
        stmt = select(Memory).where(
            Memory.organization_id == org_id,
            Memory.id == memory_id,
            Memory.is_deleted == False,
        )
        return self.db.scalar(stmt)

    def list_active(
        self,
        org_id: int,
        agent_id: int | None = None,
        memory_type: str | None = None,
    ) -> list[Memory]:
        """List active memories for specific filters."""
        stmt = select(Memory).where(
            Memory.organization_id == org_id,
            Memory.is_deleted == False,
        )
        if agent_id is not None:
            stmt = stmt.where(Memory.agent_id == agent_id)
        if memory_type is not None:
            stmt = stmt.where(Memory.memory_type == memory_type)

        return list(self.db.scalars(stmt).all())
