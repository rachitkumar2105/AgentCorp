"""
Team membership model.
"""

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base_model import BaseModel


class TeamMember(Base, BaseModel):
    """
    Associates users with teams.
    """

    __tablename__ = "team_members"

    __table_args__ = (
        UniqueConstraint(
            "team_id",
            "user_id",
            name="uq_team_user",
        ),
    )

    team_id: Mapped[int] = mapped_column(
        ForeignKey(
            "teams.id",
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

    team = relationship(
        "Team",
        back_populates="members",
    )

    user = relationship(
        "User",
        back_populates="teams",
    )