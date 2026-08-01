"""
Tool repository.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tool import Tool
from app.repositories.base_repository import BaseRepository


class ToolRepository(BaseRepository[Tool]):
    """
    Repository for Tool model operations.
    """

    def __init__(self, db: Session):
        super().__init__(Tool, db)

    def get_by_name(self, name: str) -> Tool | None:
        """
        Retrieve a tool by name.
        """
        stmt = select(Tool).where(Tool.name == name)
        return self.db.scalar(stmt)
