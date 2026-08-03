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
        # Normalize email for case-insensitive uniqueness
        email_normalized = payload.email.strip().lower()
        existing = self.repository.get_by_email(email_normalized)

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already exists.",
            )

        # Password policy: minimum length 8 characters
        if len(payload.password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters long.",
            )

        user = User(
            full_name=payload.full_name,
            email=email_normalized,
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
        # Normalize email for case‑insensitive lookup
        email_normalized = email.strip().lower()
        user = self.repository.get_by_email(email_normalized)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials.",
            )

        # Ensure the user account is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user.",
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