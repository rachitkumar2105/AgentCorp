"""
Team service dependencies.
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.team_repository import TeamRepository
from app.services.team_service import TeamService


def get_team_service(
    db: Session = Depends(get_db),
) -> TeamService:
    """
    Returns a TeamService instance.
    """
    repository = TeamRepository(db)
    return TeamService(repository)