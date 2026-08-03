"""app/services/security_policy_service.py

Business service for SecurityPolicy CRUD and active-policy retrieval.
Follows the Repository → Service → Dependency → API pattern.
"""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.security_policy import SecurityPolicy
from app.repositories.security_policy_repository import SecurityPolicyRepository
from app.security.policy_engine import invalidate_policy_cache


class SecurityPolicyService:
    """Business-logic layer for managing security policies."""

    def __init__(self, db: Session) -> None:
        self.repo = SecurityPolicyRepository(db)

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_by_id(self, policy_id: int) -> Optional[SecurityPolicy]:
        return self.repo.get(policy_id)

    def get_all(self) -> List[SecurityPolicy]:
        return self.repo.get_all()

    def get_active_policies(self) -> List[SecurityPolicy]:
        return self.repo.get_active()

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def create(
        self,
        name: str,
        resource: str,
        action: str,
        effect: str,
        condition: Optional[dict] = None,
        is_active: bool = True,
    ) -> SecurityPolicy:
        policy = SecurityPolicy(
            name=name,
            resource=resource,
            action=action,
            effect=effect,
            condition=condition,
            is_active=is_active,
        )
        created = self.repo.create(policy)
        invalidate_policy_cache()
        return created

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, policy_id: int, **kwargs) -> Optional[SecurityPolicy]:
        policy = self.repo.get(policy_id)
        if not policy:
            return None
        for key, value in kwargs.items():
            if hasattr(policy, key):
                setattr(policy, key, value)
        updated = self.repo.update(policy)
        invalidate_policy_cache()
        return updated

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete(self, policy_id: int) -> bool:
        policy = self.repo.get(policy_id)
        if not policy:
            return False
        self.repo.delete(policy)
        invalidate_policy_cache()
        return True
