"""
Workflow Engine Pydantic schemas.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field


class NodeBase(BaseModel):
    name: str
    node_type: str
    configuration: Optional[dict[str, Any]] = Field(default_factory=dict)
    timeout: float = Field(60.0, ge=1.0)


class NodeResponse(NodeBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class EdgeBase(BaseModel):
    source_node_id: int
    target_node_id: int
    transition_condition: Optional[str] = None
    priority: int = 0


class EdgeResponse(EdgeBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class WorkflowBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    version: str = "1.0.0"


class WorkflowCreate(WorkflowBase):
    nodes: list[NodeBase] = Field(default_factory=list)
    edges: list[EdgeBase] = Field(default_factory=list)


class WorkflowResponse(WorkflowBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    status: str
    enabled: bool
    created_by: int
    created_at: datetime
    updated_at: datetime


class ExecutionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workflow_id: int
    status: str
    current_node_id: Optional[int] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration: Optional[float] = None
    execution_context: dict[str, Any]
