"""
System metric database model.
"""

from typing import Any, Dict
from sqlalchemy import String, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base_model import BaseModel


class SystemMetric(Base, BaseModel):
    """
    Represents system counter, gauge, or histogram measurements.
    """

    __tablename__ = "system_metrics"

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    metric_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    value: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    tags: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )
