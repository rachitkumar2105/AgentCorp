"""
Seed default roles and permissions.
"""

from sqlalchemy.orm import Session

from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission


DEFAULT_ROLES = [
    "Admin",
    "Manager",
    "User",
]


DEFAULT_PERMISSIONS = [
    "role:create",
    "role:read",
    "role:update",
    "role:delete",
    "role:assign",
    "permission:create",
    "permission:read",
    "permission:update",
    "permission:delete",
    "permission:assign",
]


def seed(db: Session):

    roles = {}

    for name in DEFAULT_ROLES:

        role = db.query(Role).filter(
            Role.name == name
        ).first()

        if role is None:
            role = Role(name=name)
            db.add(role)
            db.flush()

        roles[name] = role

    permissions = {}

    for name in DEFAULT_PERMISSIONS:

        permission = db.query(Permission).filter(
            Permission.name == name
        ).first()

        if permission is None:
            permission = Permission(name=name)
            db.add(permission)
            db.flush()

        permissions[name] = permission

    admin = roles["Admin"]

    for permission in permissions.values():

        exists = db.query(RolePermission).filter(
            RolePermission.role_id == admin.id,
            RolePermission.permission_id == permission.id,
        ).first()

        if exists is None:
            db.add(
                RolePermission(
                    role_id=admin.id,
                    permission_id=permission.id,
                )
            )

    db.commit()