"""app/api/v1/security.py

Security, Governance & Compliance API endpoints.

Endpoints:
  Policies:
    GET    /api/v1/security/policies
    POST   /api/v1/security/policies
    GET    /api/v1/security/policies/{policy_id}
    PUT    /api/v1/security/policies/{policy_id}
    DELETE /api/v1/security/policies/{policy_id}

  Quotas:
    GET    /api/v1/security/quotas/{entity_id}/{quota_type}
    POST   /api/v1/security/quotas/{entity_id}/{quota_type}/reset

  Audit Events:
    GET    /api/v1/security/audit-events

  PII:
    POST   /api/v1/security/pii/detect
    POST   /api/v1/security/pii/redact

  Encryption:
    POST   /api/v1/security/encrypt
    POST   /api/v1/security/decrypt

  Compliance:
    GET    /api/v1/security/compliance/export/{user_id}
    DELETE /api/v1/security/compliance/user/{user_id}
    POST   /api/v1/security/compliance/events
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_active_user, get_current_superuser
from app.dependencies.database import get_db
from app.dependencies.security import (
    get_audit_security_service,
    get_quota_service,
    get_security_policy_service,
    require_permission,
)
from app.models.user import User
from app.schemas.security import (
    AuditSecurityEventResponse,
    ComplianceEventRequest,
    DataExportResponse,
    DecryptRequest,
    DecryptResponse,
    EncryptRequest,
    EncryptResponse,
    PIIDetectionRequest,
    PIIDetectionResponse,
    PIIRedactRequest,
    PIIRedactResponse,
    QuotaResetResponse,
    QuotaUsageResponse,
    SecurityPolicyCreate,
    SecurityPolicyResponse,
    SecurityPolicyUpdate,
)
from app.services.audit_security_service import AuditSecurityService
from app.services.quota_service import QuotaService
from app.services.security_policy_service import SecurityPolicyService

router = APIRouter(prefix="/api/v1/security", tags=["security"])


# ---------------------------------------------------------------------------
# Security Policies
# ---------------------------------------------------------------------------

@router.get(
    "/policies",
    response_model=List[SecurityPolicyResponse],
    summary="List all security policies",
    dependencies=[Depends(require_permission("security:read"))],
)
def list_policies(
    svc: SecurityPolicyService = Depends(get_security_policy_service),
):
    return svc.get_all()


@router.post(
    "/policies",
    response_model=SecurityPolicyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a security policy",
    dependencies=[Depends(require_permission("security:write"))],
)
def create_policy(
    payload: SecurityPolicyCreate,
    svc: SecurityPolicyService = Depends(get_security_policy_service),
):
    return svc.create(
        name=payload.name,
        resource=payload.resource,
        action=payload.action,
        effect=payload.effect,
        condition=payload.condition,
        is_active=payload.is_active,
    )


@router.get(
    "/policies/{policy_id}",
    response_model=SecurityPolicyResponse,
    summary="Get a security policy by ID",
    dependencies=[Depends(require_permission("security:read"))],
)
def get_policy(
    policy_id: int,
    svc: SecurityPolicyService = Depends(get_security_policy_service),
):
    policy = svc.get_by_id(policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy


@router.put(
    "/policies/{policy_id}",
    response_model=SecurityPolicyResponse,
    summary="Update a security policy",
    dependencies=[Depends(require_permission("security:write"))],
)
def update_policy(
    policy_id: int,
    payload: SecurityPolicyUpdate,
    svc: SecurityPolicyService = Depends(get_security_policy_service),
):
    updated = svc.update(policy_id, **payload.model_dump(exclude_none=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Policy not found")
    return updated


@router.delete(
    "/policies/{policy_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a security policy",
    dependencies=[Depends(require_permission("security:delete"))],
)
def delete_policy(
    policy_id: int,
    svc: SecurityPolicyService = Depends(get_security_policy_service),
):
    deleted = svc.delete(policy_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Policy not found")


# ---------------------------------------------------------------------------
# Quotas
# ---------------------------------------------------------------------------

@router.get(
    "/quotas/{entity_id}/{quota_type}",
    response_model=QuotaUsageResponse,
    summary="Get quota usage for an entity",
    dependencies=[Depends(require_permission("security:read"))],
)
def get_quota(
    entity_id: int,
    quota_type: str,
    svc: QuotaService = Depends(get_quota_service),
):
    return svc.get_usage(entity_id, quota_type)


@router.post(
    "/quotas/{entity_id}/{quota_type}/reset",
    response_model=QuotaResetResponse,
    summary="Reset quota usage to zero",
    dependencies=[Depends(require_permission("security:write"))],
)
def reset_quota(
    entity_id: int,
    quota_type: str,
    svc: QuotaService = Depends(get_quota_service),
):
    quota = svc.reset(entity_id, quota_type)
    return QuotaResetResponse(message="Quota reset successfully", quota=quota)


# ---------------------------------------------------------------------------
# Audit Events
# ---------------------------------------------------------------------------

@router.get(
    "/audit-events",
    response_model=List[AuditSecurityEventResponse],
    summary="List security audit events",
    dependencies=[Depends(require_permission("security:audit"))],
)
def list_audit_events(
    user_id: Optional[int] = Query(None),
    organization_id: Optional[int] = Query(None),
    event_type: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    svc: AuditSecurityService = Depends(get_audit_security_service),
):
    return svc.get_events(
        user_id=user_id,
        organization_id=organization_id,
        event_type=event_type,
        limit=limit,
        offset=offset,
    )


# ---------------------------------------------------------------------------
# PII Detection & Redaction
# ---------------------------------------------------------------------------

@router.post(
    "/pii/detect",
    response_model=PIIDetectionResponse,
    summary="Detect PII in a text string",
    dependencies=[Depends(get_current_active_user)],
)
def detect_pii_endpoint(payload: PIIDetectionRequest):
    from app.security.pii import detect_pii, contains_pii
    detections = detect_pii(payload.text)
    return PIIDetectionResponse(
        detections=detections,
        contains_pii=bool(detections),
    )


@router.post(
    "/pii/redact",
    response_model=PIIRedactResponse,
    summary="Redact PII from a text string",
    dependencies=[Depends(get_current_active_user)],
)
def redact_pii_endpoint(payload: PIIRedactRequest):
    from app.security.pii import redact_pii
    redacted = redact_pii(
        payload.text,
        pii_types=payload.pii_types,
        replacement=payload.replacement,
    )
    return PIIRedactResponse(redacted_text=redacted)


# ---------------------------------------------------------------------------
# Encryption
# ---------------------------------------------------------------------------

@router.post(
    "/encrypt",
    response_model=EncryptResponse,
    summary="Encrypt a value using the platform encryption key",
    dependencies=[Depends(require_permission("security:encrypt"))],
)
def encrypt_endpoint(payload: EncryptRequest):
    from app.security.encryption import encrypt
    return EncryptResponse(token=encrypt(payload.value))


@router.post(
    "/decrypt",
    response_model=DecryptResponse,
    summary="Decrypt a token using the platform encryption key",
    dependencies=[Depends(require_permission("security:encrypt"))],
)
def decrypt_endpoint(payload: DecryptRequest):
    from app.security.encryption import decrypt
    from cryptography.fernet import InvalidToken
    try:
        return DecryptResponse(value=decrypt(payload.token))
    except InvalidToken:
        raise HTTPException(status_code=400, detail="Invalid or tampered encryption token")


# ---------------------------------------------------------------------------
# Compliance
# ---------------------------------------------------------------------------

@router.get(
    "/compliance/export/{user_id}",
    response_model=DataExportResponse,
    summary="Export all data for a user (GDPR Art. 20)",
    dependencies=[Depends(require_permission("security:compliance"))],
)
def export_user_data(
    user_id: int,
    db: Session = Depends(get_db),
):
    from app.compliance import export_user_data as _export
    data = _export(db, user_id)
    return DataExportResponse(
        user_id=user_id,
        exported_at=datetime.utcnow(),
        data=data,
    )


@router.delete(
    "/compliance/user/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete all data for a user (GDPR Art. 17 – right to erasure)",
    dependencies=[Depends(require_permission("security:compliance"))],
)
def delete_user_data(
    user_id: int,
    db: Session = Depends(get_db),
):
    from app.compliance import delete_user_data as _delete
    _delete(db, user_id)


@router.post(
    "/compliance/events",
    status_code=status.HTTP_201_CREATED,
    summary="Log a compliance event",
    dependencies=[Depends(require_permission("security:audit"))],
)
def log_compliance_event(
    payload: ComplianceEventRequest,
    db: Session = Depends(get_db),
):
    from app.compliance import log_compliance_event as _log
    _log(db, payload.event_type, payload.details)
    return {"message": "Compliance event logged"}
