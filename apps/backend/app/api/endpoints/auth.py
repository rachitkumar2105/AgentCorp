from fastapi import APIRouter

from app.dependencies.database import DatabaseSession
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserProfile,
)
from app.services.auth_service import AuthService

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserProfile,
)
def register(
    payload: RegisterRequest,
    db: DatabaseSession,
):
    repository = UserRepository(db)
    service = AuthService(repository)

    return service.register(payload)


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    payload: LoginRequest,
    db: DatabaseSession,
):
    repository = UserRepository(db)
    service = AuthService(repository)

    token = service.login(
        payload.email,
        payload.password,
    )

    return TokenResponse(
        access_token=token
    )