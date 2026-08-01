"""
Team member repository.
"""

from sqlalchemy.orm import Session

from app.models.team_member import TeamMember
from app.repositories.base_repository import BaseRepository


class TeamMemberRepository(BaseRepository[TeamMember]):
    """
    Repository for TeamMember operations.
    """

    def __init__(self, db: Session):
        super().__init__(TeamMember, db)

    def get_member(
        self,
        team_id: int,
        user_id: int,
    ) -> TeamMember | None:
        return (
            self.db.query(TeamMember)
            .filter(
                TeamMember.team_id == team_id,
                TeamMember.user_id == user_id,
            )
            .first()
        )

    def get_team_members(
        self,
        team_id: int,
    ) -> list[TeamMember]:
        return (
            self.db.query(TeamMember)
            .filter(
                TeamMember.team_id == team_id
            )
            .all()
        )