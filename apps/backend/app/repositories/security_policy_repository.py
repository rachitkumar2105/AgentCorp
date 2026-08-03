"""app/repositories/security_policy_repository.py

Repository for the SecurityPolicy model.
Extends BaseRepository with security-specific queries.
"""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.security_policy import SecurityPolicy
from app.repositories.base_repository import BaseRepository


class SecurityPolicyRepository(BaseRepository[SecurityPolicy]):
    """Repository for SecurityPolicy entities."""

    def __init__(self, db: Session) -> None:
        super().__init__(SecurityPolicy, db)

    def get_active(self) -> List[SecurityPolicy]:
        """Return all policies where ``is_active`` is True."""
        stmt = select(SecurityPolicy).where(SecurityPolicy.is_active.is_(True))
        return list(self.db.scalars(stmt).all())

    def get_by_name(self, name: str) -> Optional[SecurityPolicy]:
        """Return a policy by its unique name."""
        stmt = select(SecurityPolicy).where(SecurityPolicy.name == name)
        return self.db.scalar(stmt)

    def get_for_resource(self, resource: str, action: str) -> List[SecurityPolicy]:
        """Return all active policies matching *resource* and *action*."""
        stmt = (
            select(SecurityPolicy)
            .where(
                SecurityPolicy.resource == resource,
                SecurityPolicy.action == action,
                SecurityPolicy.is_active.is_(True),
            )
        )
        return list(self.db.scalars(stmt).all())
