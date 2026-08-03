"""app/compliance.py

Compliance service layer (GDPR / CCPA and general audit compliance).

Orchestrates data export, user data deletion, PII reporting, and audit logging.
All persistence is done through the repository layer; no direct DB access here.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.security.governance import export_entity_data, log_governance_event, soft_delete
from app.security.pii import detect_pii, redact_pii


# ---------------------------------------------------------------------------
# Data subject rights (GDPR Art. 15, 17, 20)
# ---------------------------------------------------------------------------

def export_user_data(db: Session, user_id: int) -> Dict[str, List[Dict]]:
    """Export all data associated with *user_id* (GDPR Article 20 – portability).

    Args:
        db: SQLAlchemy session.
        user_id: ID of the user requesting export.

    Returns:
        Dict mapping entity type → list of serialised rows.
    """
    data = export_entity_data(db, user_id)
    log_governance_event(
        db,
        event_type="data_export",
        user_id=user_id,
        details={"tables": list(data.keys()), "timestamp": datetime.utcnow().isoformat()},
    )
    return data


def delete_user_data(db: Session, user_id: int) -> None:
    """Perform a GDPR Article 17 erasure request.

    Soft-deletes the user record and logs the event. A background job
    will perform the hard purge after the retention grace period.
    """
    from app.models.user import User

    user = db.query(User).filter_by(id=user_id).first()
    if user:
        soft_delete(user)
        db.commit()

    log_governance_event(
        db,
        event_type="user_data_deletion",
        user_id=user_id,
        details={"action": "soft_delete", "timestamp": datetime.utcnow().isoformat()},
    )


# ---------------------------------------------------------------------------
# PII compliance
# ---------------------------------------------------------------------------

def scan_for_pii(text: str) -> List[Dict[str, str]]:
    """Return a list of PII detections in *text*.

    Useful for pre-flight checks on user content before storing or processing it.
    """
    return detect_pii(text)


def sanitize_for_storage(text: str) -> str:
    """Redact all PII from *text* before storing it in the database."""
    return redact_pii(text)


# ---------------------------------------------------------------------------
# Compliance event audit
# ---------------------------------------------------------------------------

def log_compliance_event(db: Session, event_type: str, details: Dict[str, Any]) -> None:
    """Create an audit entry for a compliance-related action.

    Args:
        db: SQLAlchemy session.
        event_type: Short identifier (e.g., ``"consent_updated"``).
        details: Arbitrary context dict (will be stored as JSON).
    """
    log_governance_event(
        db,
        event_type=event_type,
        user_id=details.get("user_id"),
        details=details,
    )
