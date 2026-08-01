"""
Tool schemas.
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class ToolBase(BaseModel):
    """
    Base Tool schema.
    """

    name: str = Field(
        ...,
        max_length=100,
        description="Name of the tool",
    )
    description: str = Field(
        ...,
        description="Detailed description of what the tool does",
    )


class ToolCreate(ToolBase):
    """
    Schema for creating a tool.
    """

    pass


class ToolUpdate(BaseModel):
    """
    Schema for updating a tool.
    """

    name: str | None = Field(
        default=None,
        max_length=100,
    )
    description: str | None = None


class ToolResponse(ToolBase):
    """
    Response schema for Tool.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
