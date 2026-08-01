"""
Multi-Agent Collaboration System — Database Models.

Tables:
    multi_agent_sessions     — Collaboration session header
    multi_agent_participants — Agents enrolled in a session
    agent_inter_messages     — Persisted inter-agent messages
    agent_delegations        — Task delegation records
"""

from __future__ import annotations

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base_model import BaseModel


class MultiAgentSession(Base, BaseModel):
    """
    Top-level collaboration session tying a coordinator agent and peers
    together around a shared goal.
    """

    __tablename__ = "multi_agent_sessions"

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    coordinator_agent_id: Mapped[int] = mapped_column(
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    goal: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), default="PENDING", nullable=False, index=True
    )
    shared_context: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    participants = relationship(
        "MultiAgentParticipant",
        back_populates="session",
        cascade="all, delete-orphan",
    )
    inter_messages = relationship(
        "AgentInterMessage",
        back_populates="session",
        cascade="all, delete-orphan",
    )
    delegations = relationship(
        "AgentDelegation",
        back_populates="session",
        cascade="all, delete-orphan",
    )


class MultiAgentParticipant(Base, BaseModel):
    """
    Maps an agent into a multi-agent session with an assigned role and
    status tracking.
    """

    __tablename__ = "multi_agent_participants"

    session_id: Mapped[int] = mapped_column(
        ForeignKey("multi_agent_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    agent_id: Mapped[int] = mapped_column(
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(
        String(100), default="worker", nullable=False
    )  # "coordinator" | "worker" | "reviewer"
    sub_task: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), default="PENDING", nullable=False
    )
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    session = relationship("MultiAgentSession", back_populates="participants")


class AgentInterMessage(Base, BaseModel):
    """
    Persistent record of every inter-agent message routed through the
    message bus within a session.
    """

    __tablename__ = "agent_inter_messages"

    session_id: Mapped[int] = mapped_column(
        ForeignKey("multi_agent_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    from_agent_id: Mapped[int] = mapped_column(
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
    )
    to_agent_id: Mapped[int | None] = mapped_column(
        ForeignKey("agents.id", ondelete="SET NULL"),
        nullable=True,
    )  # NULL = broadcast to all participants
    message_type: Mapped[str] = mapped_column(
        String(100), default="text", nullable=False
    )  # "text" | "result" | "error" | "status" | "broadcast"
    content: Mapped[dict] = mapped_column(JSON, nullable=False)
    delivered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    session = relationship("MultiAgentSession", back_populates="inter_messages")


class AgentDelegation(Base, BaseModel):
    """
    Records a task delegation from one agent to another within a session.
    """

    __tablename__ = "agent_delegations"

    session_id: Mapped[int] = mapped_column(
        ForeignKey("multi_agent_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    from_agent_id: Mapped[int] = mapped_column(
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
    )
    to_agent_id: Mapped[int] = mapped_column(
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
    )
    task_description: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    delegation_depth: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), default="PENDING", nullable=False
    )  # "PENDING" | "ACCEPTED" | "COMPLETED" | "FAILED"
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    session = relationship("MultiAgentSession", back_populates="delegations")
