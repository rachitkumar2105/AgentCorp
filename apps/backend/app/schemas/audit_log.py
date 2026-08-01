"""
Audit log schema definition.
"""

from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict


class AuditLogBase(BaseModel):
    action: str
    resource: str
    resource_id: Optional[str] = None
    actor_id: Optional[int] = None
    organization_id: Optional[int] = None
    status: str = "success"
    ip_address: Optional[str] = None
    extra_metadata: Dict[str, Any] = {}


class AuditLogCreate(AuditLogBase):
    pass


class AuditLogOut(AuditLogBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
