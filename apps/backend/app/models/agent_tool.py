"""
Agent tool mapping model.
"""

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base_model import BaseModel


class AgentTool(Base, BaseModel):
    """
    Maps tools assigned to an agent.
    """

    __tablename__ = "agent_tools"

    __table_args__ = (
        UniqueConstraint(
            "agent_id",
            "tool_id",
            name="uq_agent_tool",
        ),
    )

    agent_id: Mapped[int] = mapped_column(
        ForeignKey(
            "agents.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    tool_id: Mapped[int] = mapped_column(
        ForeignKey(
            "tools.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    agent = relationship(
        "Agent",
        back_populates="tools",
    )

    tool = relationship(
        "Tool",
        back_populates="agents",
    )

    def __repr__(self) -> str:
        return (
            f"<AgentTool(agent={self.agent_id}, tool={self.tool_id})>"
        )