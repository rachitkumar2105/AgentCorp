"""
Organization membership schemas.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class OrganizationMemberBase(BaseModel):
    """
    Base organization membership schema.
    """

    organization_id: int
    user_id: int


class OrganizationMemberCreate(OrganizationMemberBase):
    """
    Create organization membership.
    """

    pass


class OrganizationMemberResponse(OrganizationMemberBase):
    """
    Organization membership response.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime