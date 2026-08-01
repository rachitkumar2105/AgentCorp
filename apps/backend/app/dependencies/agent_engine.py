"""
FastAPI dependency injection for AgentEngineService.
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.agent_engine_service import AgentEngineService


def get_agent_engine_service(
    db: Session = Depends(get_db),
) -> AgentEngineService:
    """Builds AgentEngineService instance for requests."""
    return AgentEngineService(db)
