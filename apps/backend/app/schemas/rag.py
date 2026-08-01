"""
RAG Engine — Pydantic v2 schemas.
"""

from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    knowledge_base_id: int
    query: str
    top_k: int = Field(5, ge=1, le=50)


class SearchResultItem(BaseModel):
    chunk_id: int
    score: float
    text: str
    metadata: dict[str, Any]


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResultItem]
