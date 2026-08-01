"""
Multi-Agent Collaboration System — Pydantic Schemas (v2).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ────────────────────────────────────────────────────────────────────────────
# Request schemas
# ────────────────────────────────────────────────────────────────────────────

class SessionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=255, description="Human-readable session name")
    goal: str = Field(..., min_length=1, description="High-level collaborative goal")
    coordinator_agent_id: int = Field(..., description="ID of the coordinating agent")
    participant_agent_ids: list[int] = Field(
        ..., min_length=1, description="IDs of worker agents to invite"
    )
    shared_context: dict[str, Any] | None = Field(
        default=None, description="Initial shared context seed"
    )


class SessionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, max_length=255)
    goal: str | None = None
    shared_context: dict[str, Any] | None = None


class DelegateTask(BaseModel):
    model_config = ConfigDict(extra="forbid")

    from_agent_id: int = Field(..., description="Agent initiating the delegation")
    to_agent_id: int = Field(..., description="Agent receiving the task")
    task_description: str = Field(..., min_length=1, description="Task to delegate")
    context: dict[str, Any] | None = Field(default=None, description="Context passed to delegate")


class SendMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    from_agent_id: int = Field(..., description="Sender agent ID")
    to_agent_id: int | None = Field(
        default=None, description="Target agent ID; None = broadcast"
    )
    message_type: str = Field(
        default="text",
        description="Message type: text | result | error | status | broadcast",
    )
    content: dict[str, Any] = Field(..., description="Message payload")


class UpdateParticipantStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")

    agent_id: int
    status: str = Field(
        ..., description="New participant status: PENDING | RUNNING | COMPLETED | FAILED"
    )
    result: dict[str, Any] | None = None


class UpdateContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    updates: dict[str, Any] = Field(..., description="Partial context updates to merge")


# ────────────────────────────────────────────────────────────────────────────
# Response schemas
# ────────────────────────────────────────────────────────────────────────────

class ParticipantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    agent_id: int
    role: str
    sub_task: str | None
    status: str
    result: dict[str, Any] | None
    joined_at: datetime
    completed_at: datetime | None


class AgentInterMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    from_agent_id: int
    to_agent_id: int | None
    message_type: str
    content: dict[str, Any]
    delivered: bool
    created_at: datetime


class AgentDelegationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    from_agent_id: int
    to_agent_id: int
    task_description: str
    context: dict[str, Any]
    delegation_depth: int
    status: str
    result: dict[str, Any] | None
    resolved_at: datetime | None
    created_at: datetime


class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    coordinator_agent_id: int
    name: str
    goal: str
    status: str
    shared_context: dict[str, Any]
    result: dict[str, Any] | None
    started_at: datetime | None
    completed_at: datetime | None
    duration: float | None
    created_by: int
    created_at: datetime
    updated_at: datetime
    participants: list[ParticipantResponse] = []


class SessionListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    coordinator_agent_id: int
    name: str
    goal: str
    status: str
    created_at: datetime
