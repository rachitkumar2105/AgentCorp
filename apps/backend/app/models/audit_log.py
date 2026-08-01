"""
Audit log database model.
"""

from typing import Any, Dict
from sqlalchemy import String, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base_model import BaseModel


class AuditLog(Base, BaseModel):
    """
    Represents an immutable record of system actions/events for compliance and security auditing.
    """

    __tablename__ = "audit_logs"

    action: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    resource: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    resource_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    actor_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True,
    )

    organization_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="success",
        nullable=False,
    )

    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
    )

    extra_metadata: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )
