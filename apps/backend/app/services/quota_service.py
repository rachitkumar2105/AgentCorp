"""app/services/quota_service.py

Business service for quota management.
Wraps the lower-level quota_manager utilities with organization/user context.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.models.quota_usage import QuotaUsage
from app.security.quota_manager import (
    enforce_quota,
    get_or_create_quota,
    increment_quota,
    reset_quota,
)


class QuotaService:
    """Service for managing usage quotas per entity (user or organization)."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_usage(self, entity_id: int, quota_type: str) -> QuotaUsage:
        return get_or_create_quota(self.db, entity_id, quota_type)

    def consume(
        self,
        entity_id: int,
        quota_type: str,
        amount: int = 1,
        limit: Optional[int] = None,
    ) -> QuotaUsage:
        """Consume *amount* units and raise if the limit is exceeded."""
        return enforce_quota(self.db, entity_id, quota_type, amount, limit)

    def increment(self, entity_id: int, quota_type: str, amount: int = 1) -> QuotaUsage:
        """Increment usage without enforcing a limit (fire-and-forget)."""
        return increment_quota(self.db, entity_id, quota_type, amount)

    def reset(self, entity_id: int, quota_type: str) -> QuotaUsage:
        """Reset quota usage to zero (e.g., at the start of a new billing period)."""
        return reset_quota(self.db, entity_id, quota_type)
