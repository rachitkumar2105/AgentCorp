"""
Tool service.
"""

from app.models.tool import Tool
from app.repositories.tool_repository import ToolRepository
from app.schemas.tool import ToolCreate, ToolUpdate


class ToolService:
    """
    Business logic for tools.
    """

    def __init__(self, repository: ToolRepository):
        self.repository = repository

    def create(self, payload: ToolCreate) -> Tool:
        """
        Create a new tool.
        """
        existing = self.repository.get_by_name(payload.name)
        if existing:
            raise ValueError("A tool with this name already exists.")

        tool = Tool(
            name=payload.name,
            description=payload.description,
        )
        return self.repository.create(tool)

    def get(self, tool_id: int) -> Tool | None:
        """
        Retrieve a tool by ID.
        """
        return self.repository.get(tool_id)

    def list_all(self) -> list[Tool]:
        """
        Retrieve all tools.
        """
        return self.repository.get_all()

    def update(self, tool: Tool, payload: ToolUpdate) -> Tool:
        """
        Update a tool.
        """
        update_data = payload.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            setattr(tool, key, value)

        return self.repository.update(tool)

    def delete(self, tool: Tool) -> None:
        """
        Delete a tool.
        """
        self.repository.delete(tool)
