"""
User role service.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.role import Role
from app.models.user import User
from app.models.user_role import UserRole


class UserRoleService:
    """
    Service for assigning roles to users.
    """

    def __init__(self, db: Session):
        self.db = db

    def assign_role(
        self,
        user_id: int,
        role_id: int,
    ) -> UserRole:

        user = self.db.get(User, user_id)

        if user is None:
            raise ValueError("User not found.")

        role = self.db.get(Role, role_id)

        if role is None:
            raise ValueError("Role not found.")

        existing = self.db.scalar(
            select(UserRole).where(
                UserRole.user_id == user_id,
                UserRole.role_id == role_id,
            )
        )

        if existing:
            raise ValueError(
                "User already has this role."
            )

        assignment = UserRole(
            user_id=user_id,
            role_id=role_id,
        )

        self.db.add(assignment)
        self.db.commit()
        self.db.refresh(assignment)

        return assignment

    def remove_role(
        self,
        user_id: int,
        role_id: int,
    ) -> None:

        assignment = self.db.scalar(
            select(UserRole).where(
                UserRole.user_id == user_id,
                UserRole.role_id == role_id,
            )
        )

        if assignment is None:
            raise ValueError(
                "Role assignment not found."
            )

        self.db.delete(assignment)
        self.db.commit()