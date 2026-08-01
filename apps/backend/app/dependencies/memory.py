"""
FastAPI dependency injection for MemoryService.
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.memory_service import MemoryService


def get_memory_service(
    db: Session = Depends(get_db),
) -> MemoryService:
    """Builds MemoryService instance for requests."""
    return MemoryService(db)
