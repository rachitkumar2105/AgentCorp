"""
Association table between roles and permissions.
"""

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base_model import BaseModel


class RolePermission(Base, BaseModel):
    """
    Associates roles with permissions.
    """

    __tablename__ = "role_permissions"

    __table_args__ = (
        UniqueConstraint(
            "role_id",
            "permission_id",
            name="uq_role_permission",
        ),
    )

    role_id: Mapped[int] = mapped_column(
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    permission_id: Mapped[int] = mapped_column(
        ForeignKey("permissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    role: Mapped["Role"] = relationship(
        "Role",
        back_populates="permissions",
    )

    permission: Mapped["Permission"] = relationship(
        "Permission",
        back_populates="roles",
    )

    def __repr__(self) -> str:
        return (
            f"<RolePermission(role_id={self.role_id}, "
            f"permission_id={self.permission_id})>"
        )