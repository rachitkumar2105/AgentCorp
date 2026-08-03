"""app/schemas/security.py

Pydantic v2 schemas for the security API:
  - SecurityPolicy (CRUD)
  - QuotaUsage (read)
  - AuditSecurityEvent (read)
  - PII scanning
  - Encryption
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# SecurityPolicy schemas
# ---------------------------------------------------------------------------

class SecurityPolicyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=128, description="Unique policy name")
    resource: str = Field(..., description="Resource identifier, e.g. 'security:policy'")
    action: str = Field(..., description="Action, e.g. 'read' or 'write'")
    effect: str = Field(..., pattern="^(allow|deny|conditional)$", description="Policy effect")
    condition: Optional[Dict[str, Any]] = Field(None, description="Optional condition dict (DSL)")
    is_active: bool = Field(True, description="Whether the policy is active")


class SecurityPolicyCreate(SecurityPolicyBase):
    pass


class SecurityPolicyUpdate(BaseModel):
    name: Optional[str] = None
    resource: Optional[str] = None
    action: Optional[str] = None
    effect: Optional[str] = Field(None, pattern="^(allow|deny|conditional)$")
    condition: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class SecurityPolicyResponse(SecurityPolicyBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# QuotaUsage schemas
# ---------------------------------------------------------------------------

class QuotaUsageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    entity_id: int
    quota_type: str
    used: int
    limit: Optional[int]
    period_start: datetime
    remaining: Optional[int]
    is_exceeded: bool


class QuotaResetResponse(BaseModel):
    message: str
    quota: QuotaUsageResponse


# ---------------------------------------------------------------------------
# AuditSecurityEvent schemas
# ---------------------------------------------------------------------------

class AuditSecurityEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_type: str
    user_id: Optional[int]
    organization_id: Optional[int]
    details: Optional[Dict[str, Any]]
    timestamp: datetime


# ---------------------------------------------------------------------------
# PII schemas
# ---------------------------------------------------------------------------

class PIIDetectionRequest(BaseModel):
    text: str = Field(..., description="Text to scan for PII")


class PIIDetection(BaseModel):
    type: str
    value: str
    start: str
    end: str


class PIIDetectionResponse(BaseModel):
    detections: List[PIIDetection]
    contains_pii: bool


class PIIRedactRequest(BaseModel):
    text: str = Field(..., description="Text to redact PII from")
    replacement: str = Field("[REDACTED]", description="Replacement token")
    pii_types: Optional[List[str]] = Field(None, description="Restrict to specific PII types")


class PIIRedactResponse(BaseModel):
    redacted_text: str


# ---------------------------------------------------------------------------
# Encryption schemas
# ---------------------------------------------------------------------------

class EncryptRequest(BaseModel):
    value: str = Field(..., description="Plain text value to encrypt")


class EncryptResponse(BaseModel):
    token: str = Field(..., description="Encrypted ciphertext token")


class DecryptRequest(BaseModel):
    token: str = Field(..., description="Ciphertext token to decrypt")


class DecryptResponse(BaseModel):
    value: str = Field(..., description="Decrypted plain text value")


# ---------------------------------------------------------------------------
# Compliance / data export schemas
# ---------------------------------------------------------------------------

class DataExportResponse(BaseModel):
    user_id: int
    exported_at: datetime
    data: Dict[str, List[Dict[str, Any]]]


class ComplianceEventRequest(BaseModel):
    event_type: str
    details: Dict[str, Any] = Field(default_factory=dict)
