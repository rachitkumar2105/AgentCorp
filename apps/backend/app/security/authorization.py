"""app/security/authorization.py

Centralized authorization utilities that wrap RBAC database queries.
Provides a simple `has_permission` function used by the policy engine.
"""

from typing import Any
from sqlalchemy import select
from app.db.session import get_db
from app.models.permission import Permission
from app.models.role_permission import RolePermission
from app.models.user_role import UserRole


def has_permission(user: Any, organization: Any, permission: str) -> bool:
    """Return True if the user has the given permission.

    Args:
        user: User model instance.
        organization: Organization model instance (can be None).
        permission: Permission string, e.g. "security:read".
    """
    if getattr(user, "is_superuser", False):
        return True

    db = get_db()
    statement = (
        select(Permission)
        .join(RolePermission, Permission.id == RolePermission.permission_id)
        .join(UserRole, UserRole.role_id == RolePermission.role_id)
        .where(
            UserRole.user_id == user.id,
            Permission.name == permission,
        )
    )
    has_perm = db.scalar(statement)
    return has_perm is not None
