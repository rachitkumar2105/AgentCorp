"""
User API endpoints.
"""

from fastapi import APIRouter, HTTPException, status

from app.core.password import hash_password
from app.dependencies.database import DatabaseSession
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserResponse
from app.services.user_service import UserService

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
)
def get_user(
    user_id: int,
    db: DatabaseSession,
):
    """
    Retrieve a user by ID.
    """

    repository = UserRepository(db)
    service = UserService(repository)

    user = service.get_user(user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    return user


@router.get(
    "/",
    response_model=list[UserResponse],
)
def get_users(
    db: DatabaseSession,
):
    """
    Retrieve all users.
    """

    repository = UserRepository(db)
    service = UserService(repository)

    return service.get_all_users()


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    payload: UserCreate,
    db: DatabaseSession,
):
    """
    Create a new user.
    """

    repository = UserRepository(db)
    service = UserService(repository)

    existing = service.get_user_by_email(payload.email)

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists.",
        )

    user = User(
        full_name=payload.full_name,
        email=payload.email,
        password_hash=hash_password(payload.password),
    )

    return service.create_user(user)