"""
FastAPI dependency injection for KnowledgeService.
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.knowledge_service import KnowledgeService


def get_knowledge_service(
    db: Session = Depends(get_db),
) -> KnowledgeService:
    """Builds KnowledgeService instance for requests."""
    return KnowledgeService(db)
