"""
Team service.
"""

from app.models.team import Team
from app.repositories.team_repository import TeamRepository
from app.schemas.team import TeamCreate, TeamUpdate


class TeamService:
    """
    Service for Team business logic.
    """

    def __init__(
        self,
        repository: TeamRepository,
    ):
        self.repository = repository

    def create(
        self,
        payload: TeamCreate,
    ) -> Team:
        existing = self.repository.get_by_name(
            payload.organization_id,
            payload.name,
        )

        if existing:
            raise ValueError(
                "A team with this name already exists."
            )

        team = Team(
            organization_id=payload.organization_id,
            name=payload.name,
            description=payload.description,
        )

        return self.repository.create(team)

    def get(
        self,
        team_id: int,
    ) -> Team | None:
        return self.repository.get(team_id)

    def list(
        self,
        organization_id: int,
    ) -> list[Team]:
        return self.repository.get_by_organization(
            organization_id
        )

    def update(
        self,
        team: Team,
        payload: TeamUpdate,
    ) -> Team:
        update_data = payload.model_dump(
            exclude_unset=True
        )

        for key, value in update_data.items():
            setattr(team, key, value)

        return self.repository.update(team)

    def delete(
        self,
        team: Team,
    ) -> None:
        self.repository.delete(team)