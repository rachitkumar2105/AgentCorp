"""
FastAPI dependency injection for RAGService.
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.rag_service import RAGService


def get_rag_service(
    db: Session = Depends(get_db),
) -> RAGService:
    """Builds RAGService instance for requests."""
    return RAGService(db)
