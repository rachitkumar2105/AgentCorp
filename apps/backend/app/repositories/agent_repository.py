"""
Agent repository.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.agent import Agent
from app.repositories.base_repository import BaseRepository


class AgentRepository(BaseRepository[Agent]):
    """
    Repository for Agent model operations.
    """

    def __init__(self, db: Session):
        super().__init__(Agent, db)

    def get_by_org(self, organization_id: int) -> list[Agent]:
        """
        Retrieve all agents for an organization.
        """
        stmt = select(Agent).where(Agent.organization_id == organization_id)
        return list(self.db.scalars(stmt).all())
