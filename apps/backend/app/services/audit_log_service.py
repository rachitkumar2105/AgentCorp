"""
Audit log service implementation.
"""

from typing import Any, Dict, List
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.repositories.audit_repository import AuditRepository
from app.services.base_service import BaseService
from app.observability.audit import audit_logger


class AuditLogService(BaseService[AuditRepository]):
    """
    Service for writing, querying, and auditing security events.
    """

    def __init__(self, repository: AuditRepository):
        super().__init__(repository)
        # Register database persistence handler to global audit_logger
        audit_logger.register_handler(self._db_audit_handler)

    async def _db_audit_handler(self, event: Dict[str, Any]) -> None:
        """Handler to persist audit log events directly to database."""
        audit_log = AuditLog(
            action=event["action"],
            resource=event["resource"],
            resource_id=event["resource_id"],
            actor_id=event["actor_id"],
            organization_id=event["organization_id"],
            status=event["status"],
            ip_address=event["ip_address"],
            extra_metadata=event["extra_metadata"],
        )
        self.repository.create(audit_log)

    def get_audit_logs(
        self,
        skip: int = 0,
        limit: int = 100,
        organization_id: int | None = None,
    ) -> List[AuditLog]:
        """Fetch audit logs."""
        return self.repository.get_paginated(skip=skip, limit=limit, organization_id=organization_id)
