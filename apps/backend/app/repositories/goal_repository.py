"""
Goal Repository.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.goal import Goal
from app.repositories.base_repository import BaseRepository


class GoalRepository(BaseRepository[Goal]):
    """
    Repository for Goal database queries.
    """

    def __init__(self, db: Session):
        super().__init__(Goal, db)

    def get_by_org_and_id(self, org_id: int, goal_id: int) -> Goal | None:
        """Fetch goal scoped to organization tenant."""
        stmt = select(Goal).where(
            Goal.organization_id == org_id,
            Goal.id == goal_id,
        )
        return self.db.scalar(stmt)
