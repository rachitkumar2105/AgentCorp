"""
Memory package schemas.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class MemoryBase(BaseModel):
    title: str = Field(..., max_length=255)
    content: str = Field(...)
    memory_type: str = Field("semantic")
    importance_score: float = Field(0.5, ge=0.0, le=1.0)
    confidence_score: float = Field(0.5, ge=0.0, le=1.0)


class MemoryCreate(MemoryBase):
    agent_id: int


class MemoryUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    importance_score: Optional[float] = None
    confidence_score: Optional[float] = None


class MemoryResponse(MemoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    agent_id: int
    conversation_id: Optional[int] = None
    source: str
    created_by: int
    created_at: datetime
    updated_at: datetime
    archived: bool
