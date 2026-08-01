"""
Team member service dependencies.
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.team_member_repository import (
    TeamMemberRepository,
)
from app.services.team_member_service import (
    TeamMemberService,
)


def get_team_member_service(
    db: Session = Depends(get_db),
) -> TeamMemberService:
    """
    Returns a TeamMemberService instance.
    """
    repository = TeamMemberRepository(db)
    return TeamMemberService(repository)