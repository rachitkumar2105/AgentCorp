"""
Team schemas.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TeamBase(BaseModel):
    """
    Base Team schema.
    """

    organization_id: int

    name: str = Field(
        ...,
        max_length=255,
    )

    description: str | None = Field(
        default=None,
        max_length=500,
    )


class TeamCreate(TeamBase):
    """
    Create Team schema.
    """

    pass


class TeamUpdate(BaseModel):
    """
    Update Team schema.
    """

    name: str | None = Field(
        default=None,
        max_length=255,
    )

    description: str | None = Field(
        default=None,
        max_length=500,
    )


class TeamResponse(TeamBase):
    """
    Team response schema.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    created_at: datetime
    updated_at: datetime