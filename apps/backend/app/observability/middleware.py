"""
Observability and request logging middleware.
"""

import time
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.observability.logging import (
    set_logging_context,
    clear_logging_context,
    get_logger,
)
from app.observability.metrics import metrics

logger = get_logger(__name__)


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """
    Middleware for generating correlation and request IDs,
    measuring latency, logging requests, and capturing unhandled exceptions.
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response:
        # 1. Determine or generate Request ID & Correlation ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        correlation_id = (
            request.headers.get("X-Correlation-ID")
            or request.headers.get("Correlation-ID")
            or str(uuid.uuid4())
        )

        # 2. Extract tenant/user/session metadata if available (best effort)
        # Note: at this phase in middleware, request.state or credentials aren't resolved yet,
        # but we initialize them as None. They can be overwritten in route handlers.
        set_logging_context(
            request_id=request_id,
            correlation_id=correlation_id,
        )

        start_time = time.perf_counter()
        
        try:
            response: Response = await call_next(request)
        except Exception as exc:
            # Latency for failed requests
            duration = time.perf_counter() - start_time
            
            # Log exception cleanly (do not expose stack trace directly to client)
            logger.error(
                "Unhandled exception during request %s %s: %s",
                request.method,
                request.url.path,
                str(exc),
                exc_info=exc,
            )

            # Record API failure metrics
            await metrics.increment(
                "api_request_count",
                tags={"method": request.method, "path": request.url.path, "status": "500"},
            )
            await metrics.histogram(
                "api_request_latency_seconds",
                duration,
                tags={"method": request.method, "path": request.url.path},
            )

            # Return a safe JSON response without exposing internal details
            from fastapi.responses import JSONResponse
            response = JSONResponse(
                status_code=500,
                content={"detail": "An internal server error occurred."},
            )
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Correlation-ID"] = correlation_id
            return response
        finally:
            # Latency for successful/handled requests
            duration = time.perf_counter() - start_time

        # Record standard request metrics
        status_str = str(response.status_code)
        await metrics.increment(
            "api_request_count",
            tags={"method": request.method, "path": request.url.path, "status": status_str},
        )
        await metrics.histogram(
            "api_request_latency_seconds",
            duration,
            tags={"method": request.method, "path": request.url.path},
        )

        # Expose IDs in response headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Correlation-ID"] = correlation_id

        # Log structured request details
        logger.info(
            "%s %s %s took %.4fs",
            request.method,
            request.url.path,
            status_str,
            duration,
            extra={
                "http": {
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_seconds": duration,
                }
            },
        )

        # Clean context contextvars
        clear_logging_context()

        return response
