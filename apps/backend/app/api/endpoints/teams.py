"""
Team endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.team_repository import TeamRepository
from app.schemas.team import (
    TeamCreate,
    TeamResponse,
    TeamUpdate,
)
from app.services.team_service import TeamService

router = APIRouter(
    prefix="/teams",
    tags=["Teams"],
)


@router.post(
    "",
    response_model=TeamResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_team(
    payload: TeamCreate,
    db: Session = Depends(get_db),
):
    repository = TeamRepository(db)
    service = TeamService(repository)

    try:
        return service.create(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.get(
    "/organization/{organization_id}",
    response_model=list[TeamResponse],
)
def list_teams(
    organization_id: int,
    db: Session = Depends(get_db),
):
    repository = TeamRepository(db)
    service = TeamService(repository)

    return service.list(organization_id)


@router.get(
    "/{team_id}",
    response_model=TeamResponse,
)
def get_team(
    team_id: int,
    db: Session = Depends(get_db),
):
    repository = TeamRepository(db)
    service = TeamService(repository)

    team = service.get(team_id)

    if team is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found.",
        )

    return team


@router.put(
    "/{team_id}",
    response_model=TeamResponse,
)
def update_team(
    team_id: int,
    payload: TeamUpdate,
    db: Session = Depends(get_db),
):
    repository = TeamRepository(db)
    service = TeamService(repository)

    team = service.get(team_id)

    if team is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found.",
        )

    return service.update(team, payload)


@router.delete(
    "/{team_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_team(
    team_id: int,
    db: Session = Depends(get_db),
):
    repository = TeamRepository(db)
    service = TeamService(repository)

    team = service.get(team_id)

    if team is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found.",
        )

    service.delete(team)