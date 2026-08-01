"""
Organization member repository.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.organization_member import OrganizationMember
from app.repositories.base_repository import BaseRepository


class OrganizationMemberRepository(BaseRepository[OrganizationMember]):
    """
    Repository for organization memberships.
    """

    def __init__(self, db: Session) -> None:
        super().__init__(OrganizationMember, db)

    def get_membership(
        self,
        organization_id: int,
        user_id: int,
    ) -> OrganizationMember | None:
        stmt = select(OrganizationMember).where(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.user_id == user_id,
        )
        return self.db.scalar(stmt)

    def get_by_user(self, user_id: int) -> list[OrganizationMember]:
        stmt = select(OrganizationMember).where(
            OrganizationMember.user_id == user_id
        )
        return list(self.db.scalars(stmt).all())

    def get_by_organization(self, organization_id: int) -> list[OrganizationMember]:
        stmt = select(OrganizationMember).where(
            OrganizationMember.organization_id == organization_id
        )
        return list(self.db.scalars(stmt).all())