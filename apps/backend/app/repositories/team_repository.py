"""
Team repository.
"""

from sqlalchemy.orm import Session

from app.models.team import Team
from app.repositories.base_repository import BaseRepository


class TeamRepository(BaseRepository[Team]):
    """
    Repository for Team operations.
    """

    def __init__(self, db: Session):
        super().__init__(Team, db)

    def get_by_name(
        self,
        organization_id: int,
        name: str,
    ) -> Team | None:
        return (
            self.db.query(Team)
            .filter(
                Team.organization_id == organization_id,
                Team.name == name,
            )
            .first()
        )

    def get_by_organization(
        self,
        organization_id: int,
    ) -> list[Team]:
        return (
            self.db.query(Team)
            .filter(
                Team.organization_id == organization_id
            )
            .all()
        )