"""
Organization service.
"""

from app.models.organization import Organization
from app.repositories.organization_repository import OrganizationRepository
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationUpdate,
)


class OrganizationService:
    """
    Business logic for organizations.
    """

    def __init__(self, repository: OrganizationRepository):
        self.repository = repository

    def create(
        self,
        organization_in: OrganizationCreate,
    ) -> Organization:

        if self.repository.get_by_name(organization_in.name):
            raise ValueError("Organization name already exists.")

        if self.repository.get_by_slug(organization_in.slug):
            raise ValueError("Organization slug already exists.")

        organization = Organization(
            name=organization_in.name,
            slug=organization_in.slug,
            description=organization_in.description,
        )

        return self.repository.create(organization)

    def get(
        self,
        organization_id: int,
    ) -> Organization | None:
        return self.repository.get(organization_id)

    def get_all(self) -> list[Organization]:
        return self.repository.get_all_ordered()

    def update(
        self,
        organization: Organization,
        organization_in: OrganizationUpdate,
    ) -> Organization:

        update_data = organization_in.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            setattr(organization, key, value)

        return self.repository.update(organization)

    def delete(
        self,
        organization: Organization,
    ) -> None:
        self.repository.delete(organization)