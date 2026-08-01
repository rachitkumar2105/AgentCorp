"""
Agent tool service.
"""

from app.models.agent_tool import AgentTool
from app.repositories.agent_tool_repository import AgentToolRepository
from app.schemas.agent_tool import AgentToolCreate


class AgentToolService:
    """
    Business logic for AgentTool mapping.
    """

    def __init__(self, repository: AgentToolRepository):
        self.repository = repository

    def assign_tool(self, payload: AgentToolCreate) -> AgentTool:
        """
        Assign a tool to an agent.
        """
        existing = self.repository.get_assignment(
            agent_id=payload.agent_id,
            tool_id=payload.tool_id,
        )
        if existing:
            raise ValueError("Tool is already assigned to this agent.")

        assignment = AgentTool(
            agent_id=payload.agent_id,
            tool_id=payload.tool_id,
        )
        return self.repository.create(assignment)

    def list_agent_tools(self, agent_id: int) -> list[AgentTool]:
        """
        Retrieve all tool mappings for an agent.
        """
        return self.repository.get_by_agent(agent_id)

    def remove_tool(self, agent_id: int, tool_id: int) -> None:
        """
        Remove a tool mapping from an agent.
        """
        assignment = self.repository.get_assignment(
            agent_id=agent_id,
            tool_id=tool_id,
        )
        if not assignment:
            raise ValueError("Tool assignment not found.")

        self.repository.delete(assignment)
