"""
Memory database model schema.
"""

from __future__ import annotations

from datetime import datetime
from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base_model import BaseModel


class Memory(Base, BaseModel):
    """
    Represents semantic memory bits learned across agent runs.
    """

    __tablename__ = "memories"

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    agent_id: Mapped[int] = mapped_column(
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    conversation_id: Mapped[int | None] = mapped_column(
        ForeignKey("conversations.id", ondelete="SET NULL"),
        nullable=True,
    )
    memory_type: Mapped[str] = mapped_column(String(50), nullable=False) # short_term, long_term, episodic, semantic, working
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    importance_score: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    source: Mapped[str] = mapped_column(String(100), default="extraction", nullable=False)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
