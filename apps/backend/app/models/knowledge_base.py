"""
Knowledge Base Management System — Database models.
"""

from __future__ import annotations

from datetime import datetime
from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base_model import BaseModel


class KnowledgeBase(Base, BaseModel):
    """
    Logical container/collection for uploaded knowledge documents.
    """

    __tablename__ = "knowledge_bases"

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    visibility: Mapped[str] = mapped_column(String(50), default="private", nullable=False)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    documents = relationship(
        "KnowledgeDocument",
        back_populates="knowledge_base",
        cascade="all, delete-orphan",
    )
