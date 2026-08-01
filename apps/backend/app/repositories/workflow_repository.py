"""
Workflow Repository.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.workflow import Workflow
from app.repositories.base_repository import BaseRepository


class WorkflowRepository(BaseRepository[Workflow]):
    """
    Repository for Workflow model database queries.
    """

    def __init__(self, db: Session):
        super().__init__(Workflow, db)

    def get_by_org_and_id(self, org_id: int, workflow_id: int) -> Workflow | None:
        """Fetch active workflow in scoped tenant."""
        stmt = select(Workflow).where(
            Workflow.organization_id == org_id,
            Workflow.id == workflow_id,
        )
        return self.db.scalar(stmt)
