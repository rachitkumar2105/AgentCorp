"""
Permission dependencies.

Provides reusable dependency classes for enforcing
Role-Based Access Control (RBAC) permissions.
"""

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_active_user
from app.models.permission import Permission
from app.models.role_permission import RolePermission
from app.models.user import User
from app.models.user_role import UserRole


class RequirePermission:
    """
    Dependency for checking whether the authenticated user
    has a required permission.

    Usage:

        @router.get(...)
        def endpoint(
            current_user: User = Depends(
                RequirePermission("users:read")
            )
        ):
            ...
    """

    def __init__(self, permission_name: str):
        self.permission_name = permission_name

    def __call__(
        self,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db),
    ) -> User:
        """
        Validate that the current user has the required permission.
        Superusers automatically bypass permission checks.
        """

        # Superusers bypass all permission checks
        if current_user.is_superuser:
            return current_user

        statement = (
            select(Permission)
            .join(
                RolePermission,
                Permission.id == RolePermission.permission_id,
            )
            .join(
                UserRole,
                UserRole.role_id == RolePermission.role_id,
            )
            .where(
                UserRole.user_id == current_user.id,
                Permission.name == self.permission_name,
            )
        )

        permission = db.scalar(statement)

        if permission is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied.",
            )

        return current_user