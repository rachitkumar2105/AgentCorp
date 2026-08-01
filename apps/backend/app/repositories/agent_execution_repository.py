"""
Agent Execution Repository.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.goal import AgentExecution
from app.repositories.base_repository import BaseRepository


class AgentExecutionRepository(BaseRepository[AgentExecution]):
    """
    Repository for AgentExecution model database queries.
    """

    def __init__(self, db: Session):
        super().__init__(AgentExecution, db)

    def get_by_org_and_id(self, org_id: int, execution_id: int) -> AgentExecution | None:
        """Fetch execution run mapping by organization."""
        stmt = select(AgentExecution).where(
            AgentExecution.organization_id == org_id,
            AgentExecution.id == execution_id,
        )
        return self.db.scalar(stmt)
