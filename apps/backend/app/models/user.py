"""
User database model.
"""

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base_model import BaseModel


class User(Base, BaseModel):
    """
    Represents an application user.
    """

    __tablename__ = "users"

    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    is_superuser: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # -------------------------
    # RBAC
    # -------------------------

    roles: Mapped[list["UserRole"]] = relationship(
        "UserRole",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    # -------------------------
    # Organizations
    # -------------------------

    organizations: Mapped[list["OrganizationMember"]] = relationship(
        "OrganizationMember",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    # -------------------------
    # Teams
    # -------------------------

    teams: Mapped[list["TeamMember"]] = relationship(
        "TeamMember",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    # -------------------------
    # Conversations
    # -------------------------

    conversations = relationship(
        "Conversation",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<User(id={self.id}, email='{self.email}')>"
        )