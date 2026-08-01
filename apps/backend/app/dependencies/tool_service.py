"""
Dependency injection for ToolExecutionService.
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.tool_execution_service import ToolExecutionService


def get_tool_execution_service(
    db: Session = Depends(get_db),
) -> ToolExecutionService:
    """
    Get or build wired ToolExecutionService per request.
    """
    return ToolExecutionService(db)
