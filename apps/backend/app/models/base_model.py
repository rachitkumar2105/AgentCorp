"""
Base model for all database entities.

Every model in AgentCorp should inherit from BaseModel to ensure
consistent primary keys and timestamp fields.
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column


class BaseModel:
    """
    Abstract base model containing common fields shared by all entities.
    """

    __abstract__ = True

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        """
        String representation of the model.
        """
        return f"<{self.__class__.__name__}(id={self.id})>"