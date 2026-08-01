"""
Agent tool repository.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.agent_tool import AgentTool
from app.repositories.base_repository import BaseRepository


class AgentToolRepository(BaseRepository[AgentTool]):
    """
    Repository for AgentTool mapping operations.
    """

    def __init__(self, db: Session):
        super().__init__(AgentTool, db)

    def get_assignment(self, agent_id: int, tool_id: int) -> AgentTool | None:
        """
        Retrieve a specific tool mapping for an agent.
        """
        stmt = select(AgentTool).where(
            AgentTool.agent_id == agent_id,
            AgentTool.tool_id == tool_id,
        )
        return self.db.scalar(stmt)

    def get_by_agent(self, agent_id: int) -> list[AgentTool]:
        """
        Retrieve all tools mapped to a specific agent.
        """
        stmt = select(AgentTool).where(AgentTool.agent_id == agent_id)
        return list(self.db.scalars(stmt).all())
