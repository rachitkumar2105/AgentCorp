"""
Long-term knowledge persistence model.
"""

from __future__ import annotations

from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base_model import BaseModel


class LongTermKnowledge(Base, BaseModel):
    __tablename__ = "long_term_knowledge"

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    memory_id: Mapped[int | None] = mapped_column(ForeignKey("memories.id", ondelete="SET NULL"), nullable=True)
    knowledge_type: Mapped[str] = mapped_column(String(80), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    source: Mapped[str] = mapped_column(String(100), default="learning", nullable=False)
    provenance: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
