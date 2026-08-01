"""
Team member service.
"""

from app.models.team_member import TeamMember
from app.repositories.team_member_repository import TeamMemberRepository
from app.schemas.team_member import TeamMemberCreate


class TeamMemberService:
    """
    Service for TeamMember business logic.
    """

    def __init__(
        self,
        repository: TeamMemberRepository,
    ):
        self.repository = repository

    def add_member(
        self,
        payload: TeamMemberCreate,
    ) -> TeamMember:
        existing = self.repository.get_member(
            payload.team_id,
            payload.user_id,
        )

        if existing:
            raise ValueError(
                "User is already a member of this team."
            )

        member = TeamMember(
            team_id=payload.team_id,
            user_id=payload.user_id,
        )

        return self.repository.create(member)

    def list_members(
        self,
        team_id: int,
    ) -> list[TeamMember]:
        return self.repository.get_team_members(team_id)

    def remove_member(
        self,
        team_id: int,
        user_id: int,
    ) -> None:
        member = self.repository.get_member(
            team_id,
            user_id,
        )

        if member is None:
            raise ValueError("Member not found.")

        self.repository.delete(member)