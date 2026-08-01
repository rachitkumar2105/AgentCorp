"""
Role Permission endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.permissions import RequirePermission
from app.services.role_permission_service import (
    RolePermissionService,
)

router = APIRouter(
    prefix="/role-permissions",
    tags=["Role Permissions"],
)


@router.post("/{role_id}/{permission_id}")
def assign_permission(
    role_id: int,
    permission_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        RequirePermission("permission:assign")
    ),
):
    service = RolePermissionService(db)

    try:
        return service.assign_permission(
            role_id,
            permission_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.delete("/{role_id}/{permission_id}")
def remove_permission(
    role_id: int,
    permission_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        RequirePermission("permission:assign")
    ),
):
    service = RolePermissionService(db)

    try:
        service.remove_permission(
            role_id,
            permission_id,
        )

        return {
            "message": "Permission removed successfully."
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )