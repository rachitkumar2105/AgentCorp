"""
Workflow Execution Repository.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.workflow import WorkflowExecution
from app.repositories.base_repository import BaseRepository


class WorkflowExecutionRepository(BaseRepository[WorkflowExecution]):
    """
    Repository for WorkflowExecution model database queries.
    """

    def __init__(self, db: Session):
        super().__init__(WorkflowExecution, db)

    def get_by_org_and_id(self, org_id: int, execution_id: int) -> WorkflowExecution | None:
        """Fetch active execution inside scoping organization tenant."""
        stmt = select(WorkflowExecution).where(
            WorkflowExecution.organization_id == org_id,
            WorkflowExecution.id == execution_id,
        )
        return self.db.scalar(stmt)
