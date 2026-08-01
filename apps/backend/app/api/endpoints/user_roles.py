"""
User Role endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.permissions import RequirePermission
from app.services.user_role_service import (
    UserRoleService,
)

router = APIRouter(
    prefix="/user-roles",
    tags=["User Roles"],
)


@router.post("/{user_id}/{role_id}")
def assign_role(
    user_id: int,
    role_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        RequirePermission("role:assign")
    ),
):
    service = UserRoleService(db)

    try:
        return service.assign_role(
            user_id,
            role_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.delete("/{user_id}/{role_id}")
def remove_role(
    user_id: int,
    role_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        RequirePermission("role:assign")
    ),
):
    service = UserRoleService(db)

    try:
        service.remove_role(
            user_id,
            role_id,
        )

        return {
            "message": "Role removed successfully."
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )