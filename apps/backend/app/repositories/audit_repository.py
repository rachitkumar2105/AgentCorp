"""
Audit repository implementation.
"""

from typing import List
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.repositories.base_repository import BaseRepository


class AuditRepository(BaseRepository[AuditLog]):
    """
    Repository for managing immutable audit logs.
    """

    def __init__(self, db: Session):
        super().__init__(AuditLog, db)

    def get_paginated(
        self,
        skip: int = 0,
        limit: int = 100,
        organization_id: int | None = None,
    ) -> List[AuditLog]:
        """Retrieve paginated audit logs."""
        statement = select(self.model)
        if organization_id is not None:
            statement = statement.where(self.model.organization_id == organization_id)
        
        statement = statement.order_by(self.model.created_at.desc()).offset(skip).limit(limit)
        return list(self.db.scalars(statement).all())

    def update(self, entity: AuditLog) -> AuditLog:
        """Prohibit update operations on audit logs."""
        raise NotImplementedError("Audit logs are immutable.")

    def delete(self, entity: AuditLog) -> None:
        """Prohibit delete operations on audit logs."""
        raise NotImplementedError("Audit logs are immutable.")
