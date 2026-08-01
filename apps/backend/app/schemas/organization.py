"""
Organization Pydantic schemas.
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class OrganizationBase(BaseModel):
    """
    Base organization schema.
    """

    name: str = Field(..., max_length=255)
    slug: str = Field(..., max_length=150)
    description: str | None = Field(default=None, max_length=500)


class OrganizationCreate(OrganizationBase):
    """
    Schema for creating an organization.
    """

    pass


class OrganizationUpdate(BaseModel):
    """
    Schema for updating an organization.
    """

    name: str | None = Field(default=None, max_length=255)
    slug: str | None = Field(default=None, max_length=150)
    description: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None


class OrganizationResponse(OrganizationBase):
    """
    Organization response schema.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime