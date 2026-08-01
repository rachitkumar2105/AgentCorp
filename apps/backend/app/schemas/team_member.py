"""
Team member schemas.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TeamMemberBase(BaseModel):
    """
    Base TeamMember schema.
    """

    team_id: int
    user_id: int


class TeamMemberCreate(TeamMemberBase):
    """
    Create TeamMember schema.
    """

    pass


class TeamMemberResponse(TeamMemberBase):
    """
    TeamMember response schema.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    created_at: datetime
    updated_at: datetime