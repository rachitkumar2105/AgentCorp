"""app/middleware/security_middleware.py

Security middleware that enforces rate limiting and injects security headers
for every incoming request. Authentication and RBAC are handled at the
dependency-injection layer (per endpoint) rather than globally here, to avoid
blocking public endpoints (health checks, auth endpoints).

Pipeline:
  1. Rate limiting (per-user or per-IP)
  2. Security headers injection
  3. Request forwarded to the endpoint handler
"""
from __future__ import annotations

import logging

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.security.api_security import add_security_headers
from app.security.rate_limiter import enforce_rate_limit
from app.security.exceptions import RateLimitExceededError

logger = logging.getLogger(__name__)

# Endpoints that bypass rate limiting (public / health check paths)
_RATE_LIMIT_BYPASS_PREFIXES = (
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/v1/auth",
)


class SecurityMiddleware(BaseHTTPMiddleware):
    """FastAPI/Starlette middleware for cross-cutting security concerns.

    - **Rate limiting**: blocks requests that exceed the configured
      per-minute limit for the authenticated user or client IP.
    - **Security headers**: injects CSP, X-Frame-Options, etc. on every response.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path

        # ------------------------------------------------------------------
        # 1. Rate limiting (skip for excluded paths)
        # ------------------------------------------------------------------
        if not any(path.startswith(prefix) for prefix in _RATE_LIMIT_BYPASS_PREFIXES):
            try:
                user = getattr(request.state, "user", None)
                if user is not None:
                    identifier = f"user:{user.id}"
                else:
                    client_host = request.client.host if request.client else "unknown"
                    identifier = f"ip:{client_host}"

                enforce_rate_limit(identifier)

            except RateLimitExceededError as exc:
                logger.warning("Rate limit exceeded: %s  path=%s", identifier, path)
                return JSONResponse(
                    status_code=429,
                    content={"detail": str(exc)},
                )
            except Exception:  # pragma: no cover
                logger.exception("Unexpected error in SecurityMiddleware rate-limit check")

        # ------------------------------------------------------------------
        # 2. Call the next handler
        # ------------------------------------------------------------------
        try:
            response = await call_next(request)
        except Exception:  # pragma: no cover
            logger.exception("Unhandled exception propagated through SecurityMiddleware")
            raise

        # ------------------------------------------------------------------
        # 3. Inject security headers into the response
        # ------------------------------------------------------------------
        add_security_headers(response)

        return response
