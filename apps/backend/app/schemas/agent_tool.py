"""
Agent tool schemas.
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AgentToolBase(BaseModel):
    """
    Base AgentTool mapping schema.
    """

    agent_id: int
    tool_id: int


class AgentToolCreate(AgentToolBase):
    """
    Schema for creating an AgentTool mapping.
    """

    pass


class AgentToolResponse(AgentToolBase):
    """
    Response schema for AgentTool mapping.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
