"""
Organization member service dependencies.
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.organization_member_repository import (
    OrganizationMemberRepository,
)
from app.services.organization_member_service import (
    OrganizationMemberService,
)


def get_organization_member_service(
    db: Session = Depends(get_db),
) -> OrganizationMemberService:
    """
    Returns an OrganizationMemberService instance.
    """
    repository = OrganizationMemberRepository(db)
    return OrganizationMemberService(repository)
