"""
Team database model.
"""

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base_model import BaseModel


class Team(Base, BaseModel):
    """
    Represents a team inside an organization.
    """

    __tablename__ = "teams"

    organization_id: Mapped[int] = mapped_column(
        ForeignKey(
            "organizations.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    organization = relationship(
        "Organization",
        back_populates="teams",
    )

    members = relationship(
        "TeamMember",
        back_populates="team",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<Team(id={self.id}, name='{self.name}')>"
        )