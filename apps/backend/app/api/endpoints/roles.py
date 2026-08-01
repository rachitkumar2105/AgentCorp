"""
Role endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.role import (
    RoleCreate,
    RoleUpdate,
    RoleResponse,
)
from app.services.role_service import RoleService
from app.dependencies.permissions import RequirePermission

router = APIRouter(
    prefix="/roles",
    tags=["Roles"],
)


@router.get(
    "/",
    response_model=list[RoleResponse],
)
def get_roles(
    db: Session = Depends(get_db),
    current_user=Depends(
        RequirePermission("role:read")
    ),
):
    service = RoleService(db)
    return service.get_all_roles()


@router.get(
    "/{role_id}",
    response_model=RoleResponse,
)
def get_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        RequirePermission("role:read")
    ),
):
    service = RoleService(db)

    role = service.get_role(role_id)

    if role is None:
        raise HTTPException(
            status_code=404,
            detail="Role not found.",
        )

    return role


@router.post(
    "/",
    response_model=RoleResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_role(
    data: RoleCreate,
    db: Session = Depends(get_db),
    current_user=Depends(
        RequirePermission("role:create")
    ),
):
    service = RoleService(db)

    try:
        return service.create_role(data)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.put(
    "/{role_id}",
    response_model=RoleResponse,
)
def update_role(
    role_id: int,
    data: RoleUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(
        RequirePermission("role:update")
    ),
):
    service = RoleService(db)

    try:
        return service.update_role(
            role_id,
            data,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )


@router.delete(
    "/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        RequirePermission("role:delete")
    ),
):
    service = RoleService(db)

    try:
        service.delete_role(role_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )