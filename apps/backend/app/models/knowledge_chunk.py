"""
Knowledge Chunk database model.
"""

from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base_model import BaseModel


class KnowledgeChunk(Base, BaseModel):
    """
    Represents semantic text chunks of a processed KnowledgeDocument.
    """

    __tablename__ = "knowledge_chunks"

    document_id: Mapped[int] = mapped_column(
        ForeignKey("knowledge_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False)
    character_count: Mapped[int] = mapped_column(Integer, nullable=False)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    embedding_status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    document = relationship("KnowledgeDocument", back_populates="chunks")
