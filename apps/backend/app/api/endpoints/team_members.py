"""
Team member endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.team_member_repository import (
    TeamMemberRepository,
)
from app.schemas.team_member import (
    TeamMemberCreate,
    TeamMemberResponse,
)
from app.services.team_member_service import (
    TeamMemberService,
)

router = APIRouter(
    prefix="/team-members",
    tags=["Team Members"],
)


@router.post(
    "",
    response_model=TeamMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_team_member(
    payload: TeamMemberCreate,
    db: Session = Depends(get_db),
):
    repository = TeamMemberRepository(db)
    service = TeamMemberService(repository)

    try:
        return service.add_member(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.get(
    "/team/{team_id}",
    response_model=list[TeamMemberResponse],
)
def list_team_members(
    team_id: int,
    db: Session = Depends(get_db),
):
    repository = TeamMemberRepository(db)
    service = TeamMemberService(repository)

    return service.list_members(team_id)


@router.delete(
    "/team/{team_id}/user/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_team_member(
    team_id: int,
    user_id: int,
    db: Session = Depends(get_db),
):
    repository = TeamMemberRepository(db)
    service = TeamMemberService(repository)

    try:
        service.remove_member(team_id, user_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )