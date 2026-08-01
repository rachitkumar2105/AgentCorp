from fastapi import HTTPException, status

from app.core.jwt import create_access_token
from app.core.password import (
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import RegisterRequest


class AuthService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def register(
        self,
        payload: RegisterRequest,
    ) -> User:
        existing = self.repository.get_by_email(
            payload.email
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already exists.",
            )

        user = User(
            full_name=payload.full_name,
            email=payload.email,
            password_hash=hash_password(
                payload.password
            ),
        )

        return self.repository.create(user)

    def login(
        self,
        email: str,
        password: str,
    ) -> str:
        user = self.repository.get_by_email(email)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials.",
            )

        if not verify_password(
            password,
            user.password_hash,
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials.",
            )

        return create_access_token(
            str(user.id)
        )