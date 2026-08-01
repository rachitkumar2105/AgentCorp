"""
User service.
"""

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.base_service import BaseService


class UserService(BaseService[UserRepository]):
    """
    User business logic.
    """

    def __init__(self, repository: UserRepository):
        super().__init__(repository)

    def get_user(self, user_id: int) -> User | None:
        return self.repository.get(user_id)

    def get_all_users(self) -> list[User]:
        return self.repository.get_all()

    def get_user_by_email(self, email: str) -> User | None:
        return self.repository.get_by_email(email)

    def create_user(self, user: User) -> User:
        return self.repository.create(user)

    def update_user(self, user: User) -> User:
        return self.repository.update(user)

    def delete_user(self, user: User) -> None:
        self.repository.delete(user)