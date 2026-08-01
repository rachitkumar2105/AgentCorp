"""
Base service layer.
"""

from typing import Generic, TypeVar

from app.repositories.base_repository import BaseRepository

RepositoryType = TypeVar("RepositoryType", bound=BaseRepository)


class BaseService(Generic[RepositoryType]):
    """
    Base service implementation.
    """

    def __init__(self, repository: RepositoryType):
        self.repository = repository