"""
Role permission service.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission


class RolePermissionService:
    """
    Assign permissions to roles.
    """

    def __init__(self, db: Session):
        self.db = db

    def assign_permission(
        self,
        role_id: int,
        permission_id: int,
    ) -> RolePermission:

        role = self.db.get(Role, role_id)

        if role is None:
            raise ValueError("Role not found.")

        permission = self.db.get(
            Permission,
            permission_id,
        )

        if permission is None:
            raise ValueError(
                "Permission not found."
            )

        existing = self.db.scalar(
            select(RolePermission).where(
                RolePermission.role_id == role_id,
                RolePermission.permission_id == permission_id,
            )
        )

        if existing:
            raise ValueError(
                "Permission already assigned."
            )

        assignment = RolePermission(
            role_id=role_id,
            permission_id=permission_id,
        )

        self.db.add(assignment)
        self.db.commit()
        self.db.refresh(assignment)

        return assignment

    def remove_permission(
        self,
        role_id: int,
        permission_id: int,
    ) -> None:

        assignment = self.db.scalar(
            select(RolePermission).where(
                RolePermission.role_id == role_id,
                RolePermission.permission_id == permission_id,
            )
        )

        if assignment is None:
            raise ValueError(
                "Permission assignment not found."
            )

        self.db.delete(assignment)
        self.db.commit()