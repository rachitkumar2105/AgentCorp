"""
Organization service dependencies.
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.organization_repository import OrganizationRepository
from app.services.organization_service import OrganizationService


def get_organization_service(
    db: Session = Depends(get_db),
) -> OrganizationService:
    """
    Returns an OrganizationService instance.
    """
    repository = OrganizationRepository(db)
    return OrganizationService(repository)
