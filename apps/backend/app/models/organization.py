"""
Organization database model.
"""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base_model import BaseModel


class Organization(Base, BaseModel):
    """
    Represents a tenant organization.
    """

    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    slug: Mapped[str] = mapped_column(
        String(150),
        unique=True,
        nullable=False,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
    )

    members = relationship(
        "OrganizationMember",
        back_populates="organization",
        cascade="all, delete-orphan",
    )

    teams = relationship(
        "Team",
        back_populates="organization",
        cascade="all, delete-orphan",
    )

    agents = relationship(
        "Agent",
        back_populates="organization",
        cascade="all, delete-orphan",
    )

    conversations = relationship(
        "Conversation",
        back_populates="organization",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<Organization(id={self.id}, name='{self.name}')>"
        )