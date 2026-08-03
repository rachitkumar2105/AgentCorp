"""app/repositories/audit_security_repository.py

Repository for AuditSecurityEvent model.
Extends BaseRepository with audit-specific queries.
"""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_security_event import AuditSecurityEvent
from app.repositories.base_repository import BaseRepository


class AuditSecurityRepository(BaseRepository[AuditSecurityEvent]):
    """Repository for AuditSecurityEvent entities."""

    def __init__(self, db: Session) -> None:
        super().__init__(AuditSecurityEvent, db)

    def get_by_user(self, user_id: int, limit: int = 100) -> List[AuditSecurityEvent]:
        stmt = (
            select(AuditSecurityEvent)
            .where(AuditSecurityEvent.user_id == user_id)
            .order_by(AuditSecurityEvent.timestamp.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def get_by_organization(self, organization_id: int, limit: int = 100) -> List[AuditSecurityEvent]:
        stmt = (
            select(AuditSecurityEvent)
            .where(AuditSecurityEvent.organization_id == organization_id)
            .order_by(AuditSecurityEvent.timestamp.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def get_by_event_type(self, event_type: str, limit: int = 100) -> List[AuditSecurityEvent]:
        stmt = (
            select(AuditSecurityEvent)
            .where(AuditSecurityEvent.event_type == event_type)
            .order_by(AuditSecurityEvent.timestamp.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())
