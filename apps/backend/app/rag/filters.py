"""
RAG Engine — Filtering definitions.
"""

from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field


class MetadataFilters(BaseModel):
    """
    RAG Metadata filtering criteria.
    """

    knowledge_base_id: Optional[int] = None
    document_id: Optional[int] = None
    tags: Optional[list[str]] = Field(default_factory=list)
    language: Optional[str] = None
    document_status: Optional[str] = None
