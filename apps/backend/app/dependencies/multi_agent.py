"""
Multi-Agent Collaboration System — FastAPI Dependency.
"""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.multi_agent_service import MultiAgentService


def get_multi_agent_service(
    db: Session = Depends(get_db),
) -> MultiAgentService:
    """Construct a per-request MultiAgentService."""
    return MultiAgentService(db)
