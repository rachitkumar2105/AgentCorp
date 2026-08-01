"""
Permission service.
"""

from sqlalchemy.orm import Session

from app.models.permission import Permission
from app.repositories.permission_repository import PermissionRepository
from app.schemas.permission import (
    PermissionCreate,
    PermissionUpdate,
)


class PermissionService:
    """
    Business logic for permissions.
    """

    def __init__(self, db: Session):
        self.repository = PermissionRepository(db)

    def create_permission(
        self,
        data: PermissionCreate,
    ) -> Permission:

        existing = self.repository.get_by_name(data.name)

        if existing:
            raise ValueError("Permission already exists.")

        permission = Permission(
            name=data.name,
            description=data.description,
        )

        return self.repository.create(permission)

    def get_permission(
        self,
        permission_id: int,
    ) -> Permission | None:
        return self.repository.get(permission_id)

    def get_all_permissions(self) -> list[Permission]:
        return self.repository.get_all()

    def update_permission(
        self,
        permission_id: int,
        data: PermissionUpdate,
    ) -> Permission:

        permission = self.repository.get(permission_id)

        if permission is None:
            raise ValueError("Permission not found.")

        if data.name is not None:
            permission.name = data.name

        if data.description is not None:
            permission.description = data.description

        return self.repository.update(permission)

    def delete_permission(
        self,
        permission_id: int,
    ) -> None:

        permission = self.repository.get(permission_id)

        if permission is None:
            raise ValueError("Permission not found.")

        self.repository.delete(permission)