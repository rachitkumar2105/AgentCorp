"""app/security/governance.py

Data governance utilities:
  - Data classification
  - Retention policy enforcement
  - Soft deletion
  - Purge job helper
  - Data export helpers (GDPR / CCPA)
  - Compliance audit logging
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List

# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

CLASSIFICATION_LEVELS = ("public", "internal", "confidential", "restricted")


def classify_data(record: Any, level: str) -> None:
    """Attach a classification level to a data record.

    Args:
        record: Any Python object (typically a SQLAlchemy model instance).
        level: One of ``("public", "internal", "confidential", "restricted")``.

    Raises:
        ValueError: If *level* is not a valid classification.
    """
    if level not in CLASSIFICATION_LEVELS:
        raise ValueError(
            f"Invalid classification level '{level}'. "
            f"Must be one of {CLASSIFICATION_LEVELS}."
        )
    setattr(record, "_classification", level)


# ---------------------------------------------------------------------------
# Retention
# ---------------------------------------------------------------------------

def should_retire(record: Any, retention_days: int) -> bool:
    """Return ``True`` if *record* has exceeded its retention period.

    Expects the record to have a ``created_at`` datetime attribute.
    """
    created = getattr(record, "created_at", None) or getattr(record, "_created_at", None)
    if not isinstance(created, datetime):
        return False
    return datetime.utcnow() > created + timedelta(days=retention_days)


# ---------------------------------------------------------------------------
# Soft deletion
# ---------------------------------------------------------------------------

def soft_delete(record: Any) -> None:
    """Mark a record as logically deleted by setting ``deleted_at``."""
    setattr(record, "deleted_at", datetime.utcnow())


def is_deleted(record: Any) -> bool:
    """Return ``True`` if the record has been soft-deleted."""
    return getattr(record, "deleted_at", None) is not None


# ---------------------------------------------------------------------------
# Purge job
# ---------------------------------------------------------------------------

def purge_deleted_records(db, model_class, grace_days: int = 30) -> int:
    """Hard-delete rows that were soft-deleted at least *grace_days* ago.

    Args:
        db: SQLAlchemy session.
        model_class: The model class whose table will be purged.
        grace_days: Minimum days after soft-deletion before hard removal.

    Returns:
        Number of rows deleted.
    """
    cutoff = datetime.utcnow() - timedelta(days=grace_days)
    q = db.query(model_class).filter(
        model_class.deleted_at.isnot(None),
        model_class.deleted_at < cutoff,
    )
    count = q.delete(synchronize_session=False)
    db.commit()
    return count


# ---------------------------------------------------------------------------
# Data export (GDPR / CCPA)
# ---------------------------------------------------------------------------

def export_entity_data(db, user_id: int) -> Dict[str, List[Dict]]:
    """Collect all data associated with *user_id* for a data-subject export.

    Returns a dict mapping table names to lists of serialized row dicts.
    This is a representative implementation; extend it to cover every table
    that stores user data in your schema.
    """
    from app.models.user import User
    from app.models.conversation import Conversation
    from app.models.message import Message
    from app.models.memory import Memory
    from app.models.audit_log import AuditLog

    def _serialize(obj: Any) -> Dict:
        """Convert a SQLAlchemy row to a plain dict."""
        return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}

    result: Dict[str, List[Dict]] = {}

    user = db.query(User).filter_by(id=user_id).first()
    result["user"] = [_serialize(user)] if user else []

    conversations = db.query(Conversation).filter_by(user_id=user_id).all()
    result["conversations"] = [_serialize(c) for c in conversations]

    messages = (
        db.query(Message)
        .join(Conversation, Message.conversation_id == Conversation.id)
        .filter(Conversation.user_id == user_id)
        .all()
    )
    result["messages"] = [_serialize(m) for m in messages]

    memories = db.query(Memory).filter_by(user_id=user_id).all()
    result["memories"] = [_serialize(m) for m in memories]

    audit_logs = db.query(AuditLog).filter_by(user_id=user_id).all()
    result["audit_logs"] = [_serialize(a) for a in audit_logs]

    return result


# ---------------------------------------------------------------------------
# Compliance audit
# ---------------------------------------------------------------------------

def log_governance_event(db, event_type: str, user_id: int | None = None, details: Dict | None = None) -> None:
    """Persist a governance-related event to the audit security event table.

    Args:
        db: SQLAlchemy session.
        event_type: Short identifier for the event (e.g., ``"data_export"``).
        user_id: Optional user associated with the event.
        details: Optional dict of additional context.
    """
    from app.models.audit_security_event import AuditSecurityEvent

    event = AuditSecurityEvent(
        event_type=event_type,
        user_id=user_id,
        organization_id=None,
        details=details or {},
        timestamp=datetime.utcnow(),
    )
    db.add(event)
    db.commit()
