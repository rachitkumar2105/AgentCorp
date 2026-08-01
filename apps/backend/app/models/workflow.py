"""
Workflow Engine — Database models.
"""

from __future__ import annotations

from datetime import datetime
import sqlalchemy as sa
from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, Float, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base_model import BaseModel


class Workflow(Base, BaseModel):
    """
    Logical workflow definition schema.
    """

    __tablename__ = "workflows"

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[str] = mapped_column(String(50), default="1.0.0", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    nodes = relationship("WorkflowNode", back_populates="workflow", cascade="all, delete-orphan")
    edges = relationship("WorkflowEdge", back_populates="workflow", cascade="all, delete-orphan")
    executions = relationship("WorkflowExecution", back_populates="workflow", cascade="all, delete-orphan")


class WorkflowNode(Base, BaseModel):
    """
    Step elements inside a workflow schema graph.
    """

    __tablename__ = "workflow_nodes"

    workflow_id: Mapped[int] = mapped_column(
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    node_type: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    configuration: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    timeout: Mapped[float] = mapped_column(Float, default=60.0, nullable=False)
    retry_policy: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    workflow = relationship("Workflow", back_populates="nodes")


class WorkflowEdge(Base, BaseModel):
    """
    Directed transition edge schemas linking nodes.
    """

    __tablename__ = "workflow_edges"

    workflow_id: Mapped[int] = mapped_column(
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_node_id: Mapped[int] = mapped_column(
        ForeignKey("workflow_nodes.id", ondelete="CASCADE"),
        nullable=False,
    )
    target_node_id: Mapped[int] = mapped_column(
        ForeignKey("workflow_nodes.id", ondelete="CASCADE"),
        nullable=False,
    )
    transition_condition: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    workflow = relationship("Workflow", back_populates="edges")


class WorkflowExecution(Base, BaseModel):
    """
    Tracks runtime runs of a Workflow definition.
    """

    __tablename__ = "workflow_executions"

    workflow_id: Mapped[int] = mapped_column(
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    agent_id: Mapped[int] = mapped_column(
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
    )
    conversation_id: Mapped[int | None] = mapped_column(
        ForeignKey("conversations.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False)
    current_node_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration: Mapped[float | None] = mapped_column(Float, nullable=True)
    execution_context: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    workflow = relationship("Workflow", back_populates="executions")
    steps = relationship("WorkflowStep", back_populates="execution", cascade="all, delete-orphan")


class WorkflowStep(Base, BaseModel):
    """
    Step executions recording details for auditing.
    """

    __tablename__ = "workflow_steps"

    execution_id: Mapped[int] = mapped_column(
        ForeignKey("workflow_executions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    node_id: Mapped[int] = mapped_column(
        ForeignKey("workflow_nodes.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(50), default="RUNNING", nullable=False)
    input_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    output_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    latency_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    retries: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    execution = relationship("WorkflowExecution", back_populates="steps")
