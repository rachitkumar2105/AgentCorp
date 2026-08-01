"""
Generic repository implementation.
"""

from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Generic repository providing common CRUD operations.

    All repositories should inherit from this class and pass
    the SQLAlchemy model along with the current database session.
    """

    def __init__(
        self,
        model: type[ModelType],
        db: Session,
    ):
        self.model = model
        self.db = db

    def get(
        self,
        entity_id: int,
    ) -> ModelType | None:
        """
        Retrieve an entity by its primary key.
        """

        statement = (
            select(self.model)
            .where(self.model.id == entity_id)
        )

        return self.db.scalar(statement)

    def get_all(
        self,
    ) -> list[ModelType]:
        """
        Retrieve all entities.
        """

        statement = select(self.model)

        return list(
            self.db.scalars(statement).all()
        )

    def create(
        self,
        entity: ModelType,
    ) -> ModelType:
        """
        Persist a new entity.
        """

        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)

        return entity

    def update(
        self,
        entity: ModelType,
    ) -> ModelType:
        """
        Persist updates to an existing entity.
        """

        self.db.commit()
        self.db.refresh(entity)

        return entity

    def delete(
        self,
        entity: ModelType,
    ) -> None:
        """
        Delete an entity.
        """

        self.db.delete(entity)
        self.db.commit()

    def exists(
        self,
        entity_id: int,
    ) -> bool:
        """
        Check whether an entity exists.
        """

        return self.get(entity_id) is not None

    def save(
        self,
    ) -> None:
        """
        Commit the current transaction.
        """

        self.db.commit()

    def refresh(
        self,
        entity: ModelType,
    ) -> ModelType:
        """
        Refresh an entity from the database.
        """

        self.db.refresh(entity)

        return entity