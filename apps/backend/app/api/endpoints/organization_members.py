"""
Organization member endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_active_user
from app.dependencies.permissions import RequirePermission
from app.models.user import User
from app.models.organization_member import OrganizationMember
from app.schemas.organization_member import (
    OrganizationMemberCreate,
    OrganizationMemberResponse,
)
from app.services.dependencies.organization_member import (
    get_organization_member_service,
)
from app.services.organization_member_service import (
    OrganizationMemberService,
)

router = APIRouter(
    prefix="/organization-members",
    tags=["Organization Members"],
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
    response_model=OrganizationMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_member(
    member_in: OrganizationMemberCreate,
    db: Session = Depends(get_db),
    service: OrganizationMemberService = Depends(get_organization_member_service),
    current_user: User = Depends(RequirePermission("organization:update")),
):
    """
    Add a member to an organization (requires organization:update permission and membership).
    """
    verify_organization_membership(member_in.organization_id, current_user, db)

    try:
        return service.add_member(member_in)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.get(
    "/organization/{organization_id}",
    response_model=list[OrganizationMemberResponse],
)
def list_members(
    organization_id: int,
    db: Session = Depends(get_db),
    service: OrganizationMemberService = Depends(get_organization_member_service),
    current_user: User = Depends(get_current_active_user),
):
    """
    List all members of an organization (requires membership).
    """
    verify_organization_membership(organization_id, current_user, db)
    return service.get_organization_members(organization_id)


@router.get(
    "/user/{user_id}",
    response_model=list[OrganizationMemberResponse],
)
def list_user_organizations(
    user_id: int,
    db: Session = Depends(get_db),
    service: OrganizationMemberService = Depends(get_organization_member_service),
    current_user: User = Depends(get_current_active_user),
):
    """
    List organizations associated with a specific user (only allowed for self or superuser).
    """
    if not current_user.is_superuser and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only list your own memberships.",
        )

    return service.get_user_organizations(user_id)


@router.delete(
    "/organization/{organization_id}/user/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_member(
    organization_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    service: OrganizationMemberService = Depends(get_organization_member_service),
    current_user: User = Depends(RequirePermission("organization:update")),
):
    """
    Remove a member from an organization (requires organization:update permission and membership).
    """
    verify_organization_membership(organization_id, current_user, db)

    try:
        service.remove_member(
            organization_id=organization_id,
            user_id=user_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )