"""
Role repository.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.role import Role
from app.repositories.base_repository import BaseRepository


class RoleRepository(BaseRepository[Role]):
    """
    Repository for Role database operations.
    """

    def __init__(self, db: Session):
        super().__init__(Role, db)

    def get_by_name(self, name: str) -> Role | None:
        stmt = select(Role).where(Role.name == name)
        return self.db.scalar(stmt)

    def get_all_ordered(self) -> list[Role]:
        stmt = select(Role).order_by(Role.name)
        return list(self.db.scalars(stmt).all())