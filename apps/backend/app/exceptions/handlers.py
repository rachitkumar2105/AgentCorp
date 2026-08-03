"""app/exceptions/handlers.py

Exception handlers for the application, including specific security-related errors.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.security.exceptions import (
    SecurityError,
    AuthenticationError,
    AuthorizationError,
    PolicyViolationError,
    RateLimitExceededError,
    QuotaExceededError,
    ComplianceError,
)

# Generic handler
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )

# Specific security handlers
async def security_error_handler(request: Request, exc: SecurityError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})

async def authentication_error_handler(request: Request, exc: AuthenticationError):
    return JSONResponse(status_code=401, content={"detail": str(exc)})

async def authorization_error_handler(request: Request, exc: AuthorizationError):
    return JSONResponse(status_code=403, content={"detail": str(exc)})

async def policy_violation_error_handler(request: Request, exc: PolicyViolationError):
    return JSONResponse(status_code=403, content={"detail": str(exc)})

async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceededError):
    return JSONResponse(status_code=429, content={"detail": str(exc)})

async def quota_exceeded_handler(request: Request, exc: QuotaExceededError):
    return JSONResponse(status_code=429, content={"detail": str(exc)})

async def compliance_error_handler(request: Request, exc: ComplianceError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})

def register_exception_handlers(app: FastAPI) -> None:
    # Generic handler
    app.add_exception_handler(Exception, global_exception_handler)
    # Security related handlers
    app.add_exception_handler(SecurityError, security_error_handler)
    app.add_exception_handler(AuthenticationError, authentication_error_handler)
    app.add_exception_handler(AuthorizationError, authorization_error_handler)
    app.add_exception_handler(PolicyViolationError, policy_violation_error_handler)
    app.add_exception_handler(RateLimitExceededError, rate_limit_exceeded_handler)
    app.add_exception_handler(QuotaExceededError, quota_exceeded_handler)
    app.add_exception_handler(ComplianceError, compliance_error_handler)