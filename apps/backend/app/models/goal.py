"""
Agent Engine — Database models.
"""

from __future__ import annotations

from datetime import datetime
from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, Float, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
import sqlalchemy as sa

from app.db.base import Base
from app.models.base_model import BaseModel


class Goal(Base, BaseModel):
    """
    Goal schema defining an objective for autonomous agents.
    """

    __tablename__ = "agent_goals"

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    agent_id: Mapped[int] = mapped_column(
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    conversation_id: Mapped[int | None] = mapped_column(
        ForeignKey("conversations.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(50), default="medium", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False)
    constraints: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    success_criteria: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    tasks = relationship("GoalTask", back_populates="goal", cascade="all, delete-orphan")
    executions = relationship("AgentExecution", back_populates="goal", cascade="all, delete-orphan")


class GoalTask(Base, BaseModel):
    """
    Individual steps resulting from task decomposition.
    """

    __tablename__ = "goal_tasks"

    goal_id: Mapped[int] = mapped_column(
        ForeignKey("agent_goals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parent_task_id: Mapped[int | None] = mapped_column(
        ForeignKey("goal_tasks.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False)
    priority: Mapped[str] = mapped_column(String(50), default="medium", nullable=False)
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    estimated_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    estimated_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    execution_type: Mapped[str] = mapped_column(String(100), default="AI", nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    goal = relationship("Goal", back_populates="tasks")


class AgentExecution(Base, BaseModel):
    """
    Main execution loop run details.
    """

    __tablename__ = "agent_executions"

    goal_id: Mapped[int] = mapped_column(
        ForeignKey("agent_goals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(50), default="RUNNING", nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration: Mapped[float | None] = mapped_column(Float, nullable=True)
    execution_context: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    goal = relationship("Goal", back_populates="executions")
