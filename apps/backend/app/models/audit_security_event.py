"""app/models/audit_security_event.py

SQLAlchemy model for storing security‑related audit events.
These events capture authentication failures, policy violations, quota breaches, etc.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON
from app.db.base import Base

class AuditSecurityEvent(Base):
    __tablename__ = "audit_security_event"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String, nullable=False)  # e.g., "auth_failure", "policy_violation"
    user_id = Column(Integer, nullable=True)
    organization_id = Column(Integer, nullable=True)
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
