"""
Agent database model.
"""

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base_model import BaseModel


class Agent(Base, BaseModel):
    """
    Represents an AI Agent.
    """

    __tablename__ = "agents"

    organization_id: Mapped[int] = mapped_column(
        ForeignKey(
            "organizations.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    team_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "teams.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    system_prompt: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    model_name: Mapped[str] = mapped_column(
        String(100),
        default="gpt-4.1",
        nullable=False,
    )

    temperature: Mapped[float] = mapped_column(
        default=0.7,
        nullable=False,
    )

    max_tokens: Mapped[int] = mapped_column(
        default=4096,
        nullable=False,
    )

    is_public: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    organization = relationship(
        "Organization",
        back_populates="agents",
    )

    team = relationship(
        "Team",
        back_populates="agents",
    )

    versions = relationship(
        "AgentVersion",
        back_populates="agent",
        cascade="all, delete-orphan",
    )

    tools = relationship(
        "AgentTool",
        back_populates="agent",
        cascade="all, delete-orphan",
    )

    conversations = relationship(
        "Conversation",
        back_populates="agent",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Agent(id={self.id}, name='{self.name}')>"