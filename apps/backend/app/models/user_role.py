"""
Association table between users and roles.
"""

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base_model import BaseModel


class UserRole(Base, BaseModel):
    """
    Associates users with roles.
    """

    __tablename__ = "user_roles"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "role_id",
            name="uq_user_role",
        ),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    role_id: Mapped[int] = mapped_column(
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="roles",
    )

    role: Mapped["Role"] = relationship(
        "Role",
        back_populates="users",
    )

    def __repr__(self) -> str:
        return (
            f"<UserRole(user_id={self.user_id}, "
            f"role_id={self.role_id})>"
        )