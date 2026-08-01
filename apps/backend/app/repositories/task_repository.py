"""
Task Repository.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.goal import GoalTask
from app.repositories.base_repository import BaseRepository


class GoalTaskRepository(BaseRepository[GoalTask]):
    """
    Repository for GoalTask model database queries.
    """

    def __init__(self, db: Session):
        super().__init__(GoalTask, db)

    def list_by_goal(self, goal_id: int) -> list[GoalTask]:
        """List tasks generated for a goal."""
        stmt = select(GoalTask).where(GoalTask.goal_id == goal_id).order_by(GoalTask.order)
        return list(self.db.scalars(stmt).all())
