"""
Organization member service.
"""

from app.models.organization_member import OrganizationMember
from app.repositories.organization_member_repository import (
    OrganizationMemberRepository,
)
from app.schemas.organization_member import (
    OrganizationMemberCreate,
)


class OrganizationMemberService:
    """
    Business logic for organization memberships.
    """

    def __init__(self, repository: OrganizationMemberRepository):
        self.repository = repository

    def add_member(
        self,
        member_in: OrganizationMemberCreate,
    ) -> OrganizationMember:

        existing = self.repository.get_membership(
            organization_id=member_in.organization_id,
            user_id=member_in.user_id,
        )

        if existing:
            raise ValueError("User is already a member of this organization.")

        member = OrganizationMember(
            organization_id=member_in.organization_id,
            user_id=member_in.user_id,
        )

        return self.repository.create(member)

    def remove_member(
        self,
        organization_id: int,
        user_id: int,
    ) -> None:

        member = self.repository.get_membership(
            organization_id=organization_id,
            user_id=user_id,
        )

        if member is None:
            raise ValueError("Membership not found.")

        self.repository.delete(member)

    def get_user_organizations(
        self,
        user_id: int,
    ) -> list[OrganizationMember]:
        return self.repository.get_by_user(user_id)

    def get_organization_members(
        self,
        organization_id: int,
    ) -> list[OrganizationMember]:
        return self.repository.get_by_organization(organization_id)