from fastapi import APIRouter, Depends

from app.dependencies.auth import get_current_superuser
from app.models.user import User

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
)


@router.get("/dashboard")
def dashboard(
    current_user: User = Depends(get_current_superuser),
):
    return {
        "message": "Welcome Admin",
        "user": current_user.full_name,
    }