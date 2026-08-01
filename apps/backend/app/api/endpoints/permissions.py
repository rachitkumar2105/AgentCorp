"""
Permission endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.permissions import RequirePermission
from app.schemas.permission import (
    PermissionCreate,
    PermissionUpdate,
    PermissionResponse,
)
from app.services.permission_service import (
    PermissionService,
)

router = APIRouter(
    prefix="/permissions",
    tags=["Permissions"],
)


@router.get(
    "/",
    response_model=list[PermissionResponse],
)
def get_permissions(
    db: Session = Depends(get_db),
    current_user=Depends(
        RequirePermission("permission:read")
    ),
):
    return PermissionService(db).get_all_permissions()


@router.post(
    "/",
    response_model=PermissionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_permission(
    data: PermissionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(
        RequirePermission("permission:create")
    ),
):
    try:
        return PermissionService(db).create_permission(
            data
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.put(
    "/{permission_id}",
    response_model=PermissionResponse,
)
def update_permission(
    permission_id: int,
    data: PermissionUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(
        RequirePermission("permission:update")
    ),
):
    try:
        return PermissionService(db).update_permission(
            permission_id,
            data,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )


@router.delete(
    "/{permission_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_permission(
    permission_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        RequirePermission("permission:delete")
    ),
):
    try:
        PermissionService(db).delete_permission(
            permission_id
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )