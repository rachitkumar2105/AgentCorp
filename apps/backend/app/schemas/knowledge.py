"""
Knowledge Base Management System — Pydantic v2 schemas.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field


class KnowledgeBaseBase(BaseModel):
    name: str = Field(..., max_length=255, description="Name of the knowledge base")
    description: Optional[str] = Field(None, description="Detailed description")
    visibility: str = Field("private", description="visibility (private or shared)")


class KnowledgeBaseCreate(KnowledgeBaseBase):
    pass


class KnowledgeBaseResponse(KnowledgeBaseBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    status: str
    created_by: int
    created_at: datetime
    updated_at: datetime


class KnowledgeDocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    knowledge_base_id: int
    filename: str
    original_filename: str
    mime_type: str
    file_size: int
    checksum: str
    language: Optional[str] = None
    status: str
    processing_status: str
    page_count: Optional[int] = None
    metadata_json: Optional[dict[str, Any]] = None
    uploaded_by: int
    created_at: datetime
    updated_at: datetime
