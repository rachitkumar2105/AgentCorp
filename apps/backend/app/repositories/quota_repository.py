"""app/repositories/quota_repository.py

Repository for QuotaUsage model.
Extends BaseRepository with quota-specific queries.
"""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.quota_usage import QuotaUsage
from app.repositories.base_repository import BaseRepository


class QuotaRepository(BaseRepository[QuotaUsage]):
    """Repository for QuotaUsage entities."""

    def __init__(self, db: Session) -> None:
        super().__init__(QuotaUsage, db)

    def get_by_entity(self, entity_id: int, quota_type: str) -> Optional[QuotaUsage]:
        """Return a quota record for the given entity and type."""
        stmt = select(QuotaUsage).where(
            QuotaUsage.entity_id == entity_id,
            QuotaUsage.quota_type == quota_type,
        )
        return self.db.scalar(stmt)

    def get_all_for_entity(self, entity_id: int) -> List[QuotaUsage]:
        """Return all quota records for a given entity."""
        stmt = select(QuotaUsage).where(QuotaUsage.entity_id == entity_id)
        return list(self.db.scalars(stmt).all())
