"""
Permission repository.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.permission import Permission
from app.repositories.base_repository import BaseRepository


class PermissionRepository(BaseRepository[Permission]):
    """
    Repository for Permission database operations.
    """

    def __init__(self, db: Session):
        super().__init__(Permission, db)

    def get_by_name(self, name: str) -> Permission | None:
        stmt = select(Permission).where(Permission.name == name)
        return self.db.scalar(stmt)

    def get_all_ordered(self) -> list[Permission]:
        stmt = select(Permission).order_by(Permission.name)
        return list(self.db.scalars(stmt).all())