"""
Role service.
"""

from sqlalchemy.orm import Session

from app.models.role import Role
from app.repositories.role_repository import RoleRepository
from app.schemas.role import RoleCreate, RoleUpdate


class RoleService:
    """
    Business logic for roles.
    """

    def __init__(self, db: Session):
        self.repository = RoleRepository(db)

    def create_role(self, data: RoleCreate) -> Role:
        existing = self.repository.get_by_name(data.name)

        if existing:
            raise ValueError("Role already exists.")

        role = Role(
            name=data.name,
            description=data.description,
        )

        return self.repository.create(role)

    def get_role(self, role_id: int) -> Role | None:
        return self.repository.get(role_id)

    def get_all_roles(self) -> list[Role]:
        return self.repository.get_all()

    def update_role(
        self,
        role_id: int,
        data: RoleUpdate,
    ) -> Role:

        role = self.repository.get(role_id)

        if role is None:
            raise ValueError("Role not found.")

        if data.name is not None:
            role.name = data.name

        if data.description is not None:
            role.description = data.description

        return self.repository.update(role)

    def delete_role(self, role_id: int) -> None:
        role = self.repository.get(role_id)

        if role is None:
            raise ValueError("Role not found.")

        self.repository.delete(role)