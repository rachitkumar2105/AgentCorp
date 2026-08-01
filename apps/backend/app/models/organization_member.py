"""
Organization membership model.
"""

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base_model import BaseModel


class OrganizationMember(Base, BaseModel):
    """
    Associates users with organizations.
    """

    __tablename__ = "organization_members"

    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "user_id",
            name="uq_org_user",
        ),
    )

    organization_id: Mapped[int] = mapped_column(
        ForeignKey(
            "organizations.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    organization = relationship(
        "Organization",
        back_populates="members",
    )

    user = relationship(
        "User",
        back_populates="organizations",
    )