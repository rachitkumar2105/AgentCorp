"""app/services/audit_security_service.py

Business service for creating and querying security audit events.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.audit_security_event import AuditSecurityEvent


class AuditSecurityService:
    """Service for recording and querying security audit events."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def record(
        self,
        event_type: str,
        user_id: Optional[int] = None,
        organization_id: Optional[int] = None,
        details: Optional[dict] = None,
    ) -> AuditSecurityEvent:
        """Persist a new security audit event.

        Args:
            event_type: Short identifier, e.g. ``"auth_failure"`` or ``"policy_violation"``.
            user_id: Associated user ID (optional).
            organization_id: Associated organization ID (optional).
            details: Arbitrary JSON context.
        """
        event = AuditSecurityEvent(
            event_type=event_type,
            user_id=user_id,
            organization_id=organization_id,
            details=details or {},
            timestamp=datetime.utcnow(),
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def get_events(
        self,
        user_id: Optional[int] = None,
        organization_id: Optional[int] = None,
        event_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditSecurityEvent]:
        """Query audit events with optional filters."""
        q = self.db.query(AuditSecurityEvent)
        if user_id is not None:
            q = q.filter_by(user_id=user_id)
        if organization_id is not None:
            q = q.filter_by(organization_id=organization_id)
        if event_type:
            q = q.filter_by(event_type=event_type)
        return q.order_by(AuditSecurityEvent.timestamp.desc()).offset(offset).limit(limit).all()
