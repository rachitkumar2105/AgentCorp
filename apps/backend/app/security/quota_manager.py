"""app/security/quota_manager.py

Quota manager – tracks usage against per-entity limits (user or organization).

Uses the :class:`~app.models.quota_usage.QuotaUsage` model for persistence.
Provides helpers for:
  - Reading current usage
  - Incrementing usage
  - Resetting a quota period
  - Enforcing quota limits (raises on breach)
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.quota_usage import QuotaUsage
from app.security.constants import DEFAULT_AI_TOKENS_QUOTA
from app.security.exceptions import QuotaExceededError


# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------

def get_quota_usage(db: Session, entity_id: int, quota_type: str) -> Optional[QuotaUsage]:
    """Return the current :class:`QuotaUsage` record, or ``None`` if not found."""
    return (
        db.query(QuotaUsage)
        .filter_by(entity_id=entity_id, quota_type=quota_type)
        .first()
    )


def get_or_create_quota(db: Session, entity_id: int, quota_type: str) -> QuotaUsage:
    """Return the existing quota record, creating it with zero usage if absent."""
    usage = get_quota_usage(db, entity_id, quota_type)
    if usage is None:
        usage = QuotaUsage(
            entity_id=entity_id,
            quota_type=quota_type,
            used=0,
            limit=DEFAULT_AI_TOKENS_QUOTA,
            period_start=datetime.utcnow(),
        )
        db.add(usage)
        db.commit()
        db.refresh(usage)
    return usage


def increment_quota(db: Session, entity_id: int, quota_type: str, amount: int = 1) -> QuotaUsage:
    """Increment the usage counter by *amount*.

    Creates the record if it does not exist.
    """
    usage = get_or_create_quota(db, entity_id, quota_type)
    usage.used += amount
    db.commit()
    db.refresh(usage)
    return usage


def reset_quota(db: Session, entity_id: int, quota_type: str) -> QuotaUsage:
    """Reset the quota usage to zero and update the period start to now."""
    usage = get_or_create_quota(db, entity_id, quota_type)
    usage.used = 0
    usage.period_start = datetime.utcnow()
    db.commit()
    db.refresh(usage)
    return usage


def enforce_quota(
    db: Session,
    entity_id: int,
    quota_type: str,
    amount: int = 1,
    limit: Optional[int] = None,
) -> QuotaUsage:
    """Increment usage and raise :class:`~app.security.exceptions.QuotaExceededError` if the limit is exceeded.

    Args:
        db: Database session.
        entity_id: ID of the user or organization being checked.
        quota_type: Quota bucket identifier (e.g., ``"ai_tokens"``).
        amount: Units to consume.
        limit: Override the stored limit. Uses the record's ``limit`` field if not provided.

    Raises:
        QuotaExceededError: When usage would exceed the limit.
    """
    usage = increment_quota(db, entity_id, quota_type, amount)
    effective_limit = limit if limit is not None else (usage.limit or DEFAULT_AI_TOKENS_QUOTA)
    if usage.used > effective_limit:
        raise QuotaExceededError(
            f"Quota '{quota_type}' exceeded for entity {entity_id}: "
            f"{usage.used}/{effective_limit} units used."
        )
    return usage
