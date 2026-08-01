"""
Agent version model.
"""

from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base_model import BaseModel


class AgentVersion(Base, BaseModel):
    """
    Stores historical versions of an agent.
    """

    __tablename__ = "agent_versions"

    agent_id: Mapped[int] = mapped_column(
        ForeignKey(
            "agents.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    system_prompt: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    agent = relationship(
        "Agent",
        back_populates="versions",
    )

    def __repr__(self) -> str:
        return (
            f"<AgentVersion(agent={self.agent_id}, version={self.version})>"
        )