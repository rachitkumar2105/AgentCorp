"""
Organization API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_active_user
from app.dependencies.permissions import RequirePermission
from app.models.user import User
from app.models.organization_member import OrganizationMember
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationResponse,
    OrganizationUpdate,
)
from app.services.dependencies.organization import get_organization_service
from app.services.organization_service import OrganizationService

router = APIRouter(
    prefix="/organizations",
    tags=["Organizations"],
)


def verify_organization_membership(
    organization_id: int,
    current_user: User,
    db: Session,
) -> None:
    """
    Ensure the current user is a member of the organization, or a superuser.
    """
    if current_user.is_superuser:
        return

    membership = db.query(OrganizationMember).filter(
        OrganizationMember.organization_id == organization_id,
        OrganizationMember.user_id == current_user.id
    ).first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this organization.",
        )


@router.post(
    "/",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_organization(
    organization_in: OrganizationCreate,
    service: OrganizationService = Depends(get_organization_service),
    current_user: User = Depends(get_current_active_user),
):
    """
    Create a new organization.
    """
    try:
        return service.create(organization_in=organization_in)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.get(
    "/",
    response_model=list[OrganizationResponse],
)
def list_organizations(
    service: OrganizationService = Depends(get_organization_service),
    current_user: User = Depends(RequirePermission("organization:read")),
):
    """
    List all organizations (requires organization:read permission).
    """
    return service.get_all()


@router.get(
    "/{organization_id}",
    response_model=OrganizationResponse,
)
def get_organization(
    organization_id: int,
    db: Session = Depends(get_db),
    service: OrganizationService = Depends(get_organization_service),
    current_user: User = Depends(get_current_active_user),
):
    """
    Retrieve an organization by ID (requires membership).
    """
    verify_organization_membership(organization_id, current_user, db)

    organization = service.get(organization_id)
    if organization is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found.",
        )

    return organization


@router.put(
    "/{organization_id}",
    response_model=OrganizationResponse,
)
def update_organization(
    organization_id: int,
    organization_in: OrganizationUpdate,
    db: Session = Depends(get_db),
    service: OrganizationService = Depends(get_organization_service),
    current_user: User = Depends(RequirePermission("organization:update")),
):
    """
    Update organization details (requires organization:update permission and membership).
    """
    verify_organization_membership(organization_id, current_user, db)

    organization = service.get(organization_id)
    if organization is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found.",
        )

    return service.update(
        organization=organization,
        organization_in=organization_in,
    )


@router.delete(
    "/{organization_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_organization(
    organization_id: int,
    db: Session = Depends(get_db),
    service: OrganizationService = Depends(get_organization_service),
    current_user: User = Depends(RequirePermission("organization:delete")),
):
    """
    Delete an organization (requires organization:delete permission and membership).
    """
    verify_organization_membership(organization_id, current_user, db)

    organization = service.get(organization_id)
    if organization is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found.",
        )

    service.delete(organization)