"""app/models/security_policy.py

SQLAlchemy model representing a security policy rule.
Policies are evaluated by the policy engine to allow/deny actions.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON
from app.db.base import Base

class SecurityPolicy(Base):
    __tablename__ = "security_policy"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True, index=True)
    resource = Column(String, nullable=False)  # e.g., "security:policy"
    action = Column(String, nullable=False)   # e.g., "read", "write"
    effect = Column(String, nullable=False)  # "allow", "deny", "conditional"
    condition = Column(JSON, nullable=True)  # optional JSON condition dict
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def matches(self, user, organization, resource: str, action: str) -> bool:
        """Determine if this policy applies to the given request.
        Simple matching on resource and action; more complex logic can be
        added via the `condition` JSON.
        """
        if not self.is_active:
            return False
        if self.resource != resource:
            return False
        if self.action != action:
            return False
        # Additional condition checks can be performed by the policy engine.
        return True
