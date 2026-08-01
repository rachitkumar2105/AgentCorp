"""
Tool service dependencies.
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.agent_tool_repository import AgentToolRepository
from app.repositories.tool_repository import ToolRepository
from app.services.agent_tool_service import AgentToolService
from app.services.tool_service import ToolService


def get_tool_service(
    db: Session = Depends(get_db),
) -> ToolService:
    """
    Returns a ToolService instance.
    """
    repository = ToolRepository(db)
    return ToolService(repository)


def get_agent_tool_service(
    db: Session = Depends(get_db),
) -> AgentToolService:
    """
    Returns an AgentToolService instance.
    """
    repository = AgentToolRepository(db)
    return AgentToolService(repository)
