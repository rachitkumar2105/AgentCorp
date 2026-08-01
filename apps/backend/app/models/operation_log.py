"""
Operation log database model.
"""

from typing import Any, Dict
from sqlalchemy import String, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base_model import BaseModel


class OperationLog(Base, BaseModel):
    """
    Represents execution traces and latencies of various tasks/components.
    """

    __tablename__ = "operation_logs"

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    span_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )

    trace_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    parent_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    correlation_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    duration: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    tags: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )
