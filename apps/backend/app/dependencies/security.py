"""app/dependencies/security.py

FastAPI dependency providers for the security layer.

Provides:
  - get_security_policy_service
  - get_quota_service
  - get_audit_security_service
  - require_permission  (RBAC gate decorator/dependency)
  - check_rate_limit    (rate-limiting dependency)
"""
from __future__ import annotations
from app.security.secret_manager import SecretManager

from typing import Callable

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_active_user
from app.dependencies.database import get_db
from app.models.user import User
from app.services.security_policy_service import SecurityPolicyService
from app.services.quota_service import QuotaService
from app.services.audit_security_service import AuditSecurityService
from app.security.rate_limiter import enforce_rate_limit
from app.security.exceptions import (
    AuthorizationError,
    RateLimitExceededError,
    QuotaExceededError,
)


# ---------------------------------------------------------------------------
# Service providers
# ---------------------------------------------------------------------------

def get_security_policy_service(db: Session = Depends(get_db)) -> SecurityPolicyService:
    """Provide an instance of :class:`~app.services.security_policy_service.SecurityPolicyService`."""
    return SecurityPolicyService(db)


def get_quota_service(db: Session = Depends(get_db)) -> QuotaService:
    """Provide an instance of :class:`~app.services.quota_service.QuotaService`."""
    return QuotaService(db)


def get_audit_security_service(db: Session = Depends(get_db)) -> AuditSecurityService:
    """Provide an instance of :class:`~app.services.audit_security_service.AuditSecurityService`."""
    return AuditSecurityService(db)


# ---------------------------------------------------------------------------
# Rate limiting dependency
# ---------------------------------------------------------------------------

def check_rate_limit(request: Request, current_user: User = Depends(get_current_active_user)) -> None:
    """FastAPI dependency that enforces rate limiting per user.

    Raises HTTP 429 if the rate limit is exceeded.
    """
    identifier = f"user:{current_user.id}"
    try:
        enforce_rate_limit(identifier)
    except RateLimitExceededError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(exc),
        )


# ---------------------------------------------------------------------------
# Permission dependency factory
# ---------------------------------------------------------------------------

def require_permission(permission: str) -> Callable:
    """Return a FastAPI dependency that enforces a specific RBAC permission.

    Usage::

        @router.get("/secret", dependencies=[Depends(require_permission("security:read"))])
        def get_secret(): ...

    Args:
        permission: The permission string to enforce, e.g. ``"security:read"``.
    """
    def _dependency(
        request: Request,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db),
    ) -> User:
        # Superusers bypass permission checks
        if getattr(current_user, "is_superuser", False):
            return current_user

        from app.models.permission import Permission
        from app.models.role_permission import RolePermission
        from app.models.user_role import UserRole
        from sqlalchemy import select

        statement = (
            select(Permission)
            .join(RolePermission, Permission.id == RolePermission.permission_id)
            .join(UserRole, UserRole.role_id == RolePermission.role_id)
            .where(
                UserRole.user_id == current_user.id,
                Permission.name == permission,
            )
        )
        has_perm = db.scalar(statement)
        if not has_perm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required.",
            )
        return current_user

    return _dependency
def get_secret_manager() -> SecretManager:
    """Return a SecretManager instance for dependency injection."""
    return SecretManager()
