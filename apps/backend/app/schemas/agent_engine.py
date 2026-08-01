"""
Agent Engine Pydantic schemas.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field


class GoalBase(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    objective: str = Field(...)
    priority: str = Field("medium")
    success_criteria: Optional[str] = None


class GoalCreate(GoalBase):
    agent_id: int
    conversation_id: Optional[int] = None


class GoalResponse(GoalBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    agent_id: int
    conversation_id: Optional[int] = None
    status: str
    created_by: int
    created_at: datetime
    updated_at: datetime


class AgentExecutionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    goal_id: int
    organization_id: int
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration: Optional[float] = None
    execution_context: dict[str, Any]
