"""
FastAPI dependency injection for WorkflowService.
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.workflow_service import WorkflowService


def get_workflow_service(
    db: Session = Depends(get_db),
) -> WorkflowService:
    """Builds WorkflowService instance for requests."""
    return WorkflowService(db)
