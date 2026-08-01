"""
Organization repository.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.repositories.base_repository import BaseRepository


class OrganizationRepository(BaseRepository[Organization]):
    """
    Repository for Organization model.
    """

    def __init__(self, db: Session) -> None:
        super().__init__(Organization, db)

    def get_by_slug(self, slug: str) -> Organization | None:
        stmt = select(Organization).where(Organization.slug == slug)
        return self.db.scalar(stmt)

    def get_by_name(self, name: str) -> Organization | None:
        stmt = select(Organization).where(Organization.name == name)
        return self.db.scalar(stmt)

    def get_all_ordered(self) -> list[Organization]:
        stmt = select(Organization).order_by(Organization.created_at.desc())
        return list(self.db.scalars(stmt).all())