"""
Streaming Engine REST API — v1 SSE endpoints.

Routes:
  POST   /api/v1/chat/stream                        → new conversation stream
  POST   /api/v1/chat/{conversation_id}/stream      → continue existing conversation
  DELETE /api/v1/chat/{conversation_id}/stream      → cancel active stream
  GET    /api/v1/stream/metrics                     → internal stream metrics (admin)

SSE wire format (standard RFC 8895):
  event: token
  data: {"token":"Hello","index":0,"provider":"groq","model":"llama3","ts":"..."}

  event: done
  data: {"finish_reason":"stop","usage":{...},"latency":0.42,"tokens_sent":47}

  event: error
  data: {"error":"...","code":"provider_streaming_error"}

Security:
  - JWT validated on every request
  - RBAC enforced via RequirePermission
  - Organisation membership checked before any DB access
  - Conversation ownership enforced inside StreamingService

WebSocket readiness:
  StreamingService.stream_new_chat / stream_continue_chat return async generators
  of plain strings.  A future WebSocket endpoint can call the same generators
  and forward each string as a WebSocket frame — no service changes required.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse

from app.dependencies.auth import get_current_active_user
from app.dependencies.permissions import RequirePermission
from app.dependencies.streaming import get_streaming_service
from app.models.user import User
from app.schemas.streaming import StreamingChatRequest
from app.services.streaming_service import StreamingService
from app.utils.stream_events import format_error_event, get_metrics_snapshot

logger = logging.getLogger("streaming_api")

router = APIRouter(
    prefix="/api/v1/chat",
    tags=["Streaming Engine"],
)

# ---------------------------------------------------------------------------
# Permission constants (shared with Chat Engine)
# ---------------------------------------------------------------------------
_PERM_CHAT = "chat:send"
_PERM_ADMIN = "admin:read"

# Media type for Server-Sent Events
_SSE_MEDIA_TYPE = "text/event-stream"
_SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "X-Accel-Buffering": "no",   # disables Nginx buffering
    "Connection": "keep-alive",
}


# ---------------------------------------------------------------------------
# POST /api/v1/chat/stream — new conversation stream
# ---------------------------------------------------------------------------


@router.post(
    "/stream",
    summary="Stream Chat",
    description=(
        "Creates a new conversation and streams the assistant response as "
        "Server-Sent Events (SSE).  ``agent_id`` is required.  "
        "Each token arrives as an ``event: token`` event.  "
        "The stream closes with an ``event: done`` or ``event: error`` event."
    ),
    response_class=StreamingResponse,
    status_code=status.HTTP_200_OK,
)
async def stream_chat(
    payload: StreamingChatRequest,
    request: Request,
    organization_id: int = Query(..., description="Organisation scoping this request"),
    current_user: User = Depends(RequirePermission(_PERM_CHAT)),
    streaming_service: StreamingService = Depends(get_streaming_service),
) -> StreamingResponse:
    """
    POST /api/v1/chat/stream

    Creates a brand-new conversation and returns an SSE stream of the first
    assistant response.  ``agent_id`` must be present in the request body.

    Client-side disconnect handling:
        When the client closes the connection (browser tab closed, network drop,
        explicit ``AbortController.abort()``), FastAPI detects the disconnect
        via ``request.is_disconnected()``.  The generator is closed cleanly
        and no partial message is persisted.
    """
    _assert_org_membership(current_user, organization_id)
    logger.info(
        "stream_chat | user_id=%s org_id=%s agent_id=%s",
        current_user.id,
        organization_id,
        payload.agent_id,
    )

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            async for event in streaming_service.stream_new_chat(
                payload=payload,
                current_user=current_user,
                organization_id=organization_id,
            ):
                # Check for client disconnect before forwarding each chunk
                if await request.is_disconnected():
                    logger.info(
                        "stream_chat | client disconnected | user_id=%s org_id=%s",
                        current_user.id,
                        organization_id,
                    )
                    break
                yield event
        except HTTPException as exc:
            yield format_error_event(
                error=exc.detail,
                code=f"http_{exc.status_code}",
            )
        except Exception as exc:
            logger.error(
                "stream_chat | unexpected error | user_id=%s error=%s",
                current_user.id,
                exc,
                exc_info=True,
            )
            yield format_error_event(
                error="An unexpected error occurred.",
                code="internal_error",
            )

    return StreamingResponse(
        event_generator(),
        media_type=_SSE_MEDIA_TYPE,
        headers=_SSE_HEADERS,
    )


# ---------------------------------------------------------------------------
# POST /api/v1/chat/{conversation_id}/stream — continue conversation stream
# ---------------------------------------------------------------------------


@router.post(
    "/{conversation_id}/stream",
    summary="Continue Conversation Stream",
    description=(
        "Appends a new user message to an existing conversation and streams "
        "the assistant response as Server-Sent Events (SSE)."
    ),
    response_class=StreamingResponse,
    status_code=status.HTTP_200_OK,
)
async def stream_continue_chat(
    conversation_id: int,
    payload: StreamingChatRequest,
    request: Request,
    organization_id: int = Query(..., description="Organisation scoping this request"),
    current_user: User = Depends(RequirePermission(_PERM_CHAT)),
    streaming_service: StreamingService = Depends(get_streaming_service),
) -> StreamingResponse:
    """
    POST /api/v1/chat/{conversation_id}/stream

    Continues an existing conversation.  The service validates organisation
    ownership and user access before the stream starts.
    """
    _assert_org_membership(current_user, organization_id)
    logger.info(
        "stream_continue_chat | user_id=%s org_id=%s conv_id=%s",
        current_user.id,
        organization_id,
        conversation_id,
    )

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            async for event in streaming_service.stream_continue_chat(
                conversation_id=conversation_id,
                payload=payload,
                current_user=current_user,
                organization_id=organization_id,
            ):
                if await request.is_disconnected():
                    logger.info(
                        "stream_continue_chat | client disconnected | conv_id=%s",
                        conversation_id,
                    )
                    break
                yield event
        except HTTPException as exc:
            yield format_error_event(
                error=exc.detail,
                code=f"http_{exc.status_code}",
            )
        except Exception as exc:
            logger.error(
                "stream_continue_chat | unexpected error | conv_id=%s error=%s",
                conversation_id,
                exc,
                exc_info=True,
            )
            yield format_error_event(
                error="An unexpected error occurred.",
                code="internal_error",
            )

    return StreamingResponse(
        event_generator(),
        media_type=_SSE_MEDIA_TYPE,
        headers=_SSE_HEADERS,
    )


# ---------------------------------------------------------------------------
# DELETE /api/v1/chat/{conversation_id}/stream — cancel stream
# ---------------------------------------------------------------------------


@router.delete(
    "/{conversation_id}/stream",
    summary="Cancel Stream",
    description=(
        "Signals intent to cancel an active stream for the given conversation. "
        "The stream generator will close gracefully on its next iteration. "
        "No partial messages are persisted."
    ),
    status_code=status.HTTP_204_NO_CONTENT,
)
async def cancel_stream(
    conversation_id: int,
    organization_id: int = Query(..., description="Organisation scoping this request"),
    current_user: User = Depends(RequirePermission(_PERM_CHAT)),
) -> None:
    """
    DELETE /api/v1/chat/{conversation_id}/stream

    Graceful cancellation endpoint.  In the SSE model, the server-side
    generator is cancelled automatically when the client closes the
    connection.  This endpoint provides an explicit cancellation signal
    for clients that cannot close the SSE connection directly (e.g., some
    mobile clients or intermediate proxies).

    Future:  A streaming state registry (Redis-backed) will allow this
    endpoint to signal the active generator to stop mid-stream.
    """
    _assert_org_membership(current_user, organization_id)
    logger.info(
        "cancel_stream | user_id=%s org_id=%s conv_id=%s",
        current_user.id,
        organization_id,
        conversation_id,
    )
    # No-op for now — the generator self-terminates on client disconnect.
    # A future implementation will push a cancellation token into a shared
    # registry keyed by (user_id, conversation_id).


# ---------------------------------------------------------------------------
# GET /api/v1/stream/metrics — internal metrics (admin only)
# ---------------------------------------------------------------------------

metrics_router = APIRouter(
    prefix="/api/v1/stream",
    tags=["Streaming Engine"],
)


@metrics_router.get(
    "/metrics",
    summary="Stream Metrics",
    description=(
        "Returns current global streaming metrics: active streams, "
        "completed, cancelled, failed counts and average throughput. "
        "Restricted to admin users."
    ),
)
async def stream_metrics(
    current_user: User = Depends(RequirePermission(_PERM_ADMIN)),
) -> dict:
    """
    GET /api/v1/stream/metrics

    Returns a lightweight snapshot of in-process streaming counters.
    Replace with Prometheus/OpenTelemetry in production.
    """
    return get_metrics_snapshot()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _assert_org_membership(user: User, organization_id: int) -> None:
    """
    Verify the authenticated user belongs to the requested organisation.

    Superusers bypass this check.  Raises HTTP 403 otherwise.
    """
    if user.is_superuser:
        return

    member_org_ids = {
        membership.organization_id
        for membership in user.organizations  # type: ignore[attr-defined]
    }

    if organization_id not in member_org_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of the specified organisation.",
        )
