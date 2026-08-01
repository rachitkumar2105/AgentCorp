"""
Multi-Agent Collaboration System — v1 REST API.

Endpoints:

Session Management:
    POST   /api/v1/multi-agent/sessions              — create session
    GET    /api/v1/multi-agent/sessions              — list sessions
    GET    /api/v1/multi-agent/sessions/{id}         — get session
    POST   /api/v1/multi-agent/sessions/{id}/start   — start session
    POST   /api/v1/multi-agent/sessions/{id}/complete— complete session
    POST   /api/v1/multi-agent/sessions/{id}/cancel  — cancel session

Context:
    PATCH  /api/v1/multi-agent/sessions/{id}/context — update shared context

Delegation:
    POST   /api/v1/multi-agent/sessions/{id}/delegate        — delegate task
    GET    /api/v1/multi-agent/sessions/{id}/delegations     — list delegations
    PATCH  /api/v1/multi-agent/sessions/{id}/delegations/{d} — resolve delegation

Messaging:
    POST   /api/v1/multi-agent/sessions/{id}/messages — send message
    GET    /api/v1/multi-agent/sessions/{id}/messages — list messages

Participants:
    PATCH  /api/v1/multi-agent/sessions/{id}/participants/{agent_id}/status
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies.auth import get_current_active_user
from app.dependencies.permissions import RequirePermission
from app.dependencies.multi_agent import get_multi_agent_service
from app.models.user import User
from app.multi_agent.exceptions import (
    MultiAgentError,
    SessionNotFoundError,
    AgentNotParticipantError,
    DelegationLimitExceededError,
    DelegationNotFoundError,
)
from app.schemas.multi_agent import (
    SessionCreate,
    SessionUpdate,
    DelegateTask,
    SendMessage,
    UpdateParticipantStatus,
    UpdateContext,
    SessionResponse,
    SessionListResponse,
    AgentInterMessageResponse,
    AgentDelegationResponse,
    ParticipantResponse,
)
from app.services.multi_agent_service import MultiAgentService

logger = logging.getLogger("multi_agent_api")

router = APIRouter(
    prefix="/api/v1/multi-agent",
    tags=["Multi-Agent Collaboration"],
)

_PERM_READ = "multi_agent:read"
_PERM_WRITE = "multi_agent:write"


# ────────────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────────────

def _assert_org(user: User, organization_id: int) -> None:
    if user.is_superuser:
        return
    member_org_ids = {m.organization_id for m in user.organizations}
    if organization_id not in member_org_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of the specified organization.",
        )


def _handle_domain_error(exc: Exception) -> HTTPException:
    if isinstance(exc, SessionNotFoundError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, (AgentNotParticipantError, DelegationLimitExceededError)):
        return HTTPException(status_code=400, detail=str(exc))
    if isinstance(exc, DelegationNotFoundError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, MultiAgentError):
        return HTTPException(status_code=400, detail=str(exc))
    return HTTPException(status_code=500, detail=str(exc))


# ────────────────────────────────────────────────────────────────────────────
# Session endpoints
# ────────────────────────────────────────────────────────────────────────────

@router.post(
    "/sessions",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Multi-Agent Session",
)
def create_session(
    payload: SessionCreate,
    organization_id: int = Query(..., description="Owning organization ID"),
    current_user: User = Depends(RequirePermission(_PERM_WRITE)),
    service: MultiAgentService = Depends(get_multi_agent_service),
) -> Any:
    """Create a new multi-agent collaboration session."""
    _assert_org(current_user, organization_id)
    try:
        return service.create_session(
            organization_id=organization_id,
            coordinator_agent_id=payload.coordinator_agent_id,
            name=payload.name,
            goal=payload.goal,
            participant_agent_ids=payload.participant_agent_ids,
            shared_context=payload.shared_context,
            current_user=current_user,
        )
    except Exception as exc:
        raise _handle_domain_error(exc)


@router.get(
    "/sessions",
    response_model=list[SessionListResponse],
    summary="List Multi-Agent Sessions",
)
def list_sessions(
    organization_id: int = Query(..., description="Owning organization ID"),
    session_status: str | None = Query(default=None, alias="status"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(RequirePermission(_PERM_READ)),
    service: MultiAgentService = Depends(get_multi_agent_service),
) -> Any:
    """List collaboration sessions for an organization."""
    _assert_org(current_user, organization_id)
    return service.list_sessions(organization_id, session_status, offset, limit)


@router.get(
    "/sessions/{session_id}",
    response_model=SessionResponse,
    summary="Get Multi-Agent Session",
)
def get_session(
    session_id: int,
    organization_id: int = Query(..., description="Owning organization ID"),
    current_user: User = Depends(RequirePermission(_PERM_READ)),
    service: MultiAgentService = Depends(get_multi_agent_service),
) -> Any:
    """Retrieve a single collaboration session with participants."""
    _assert_org(current_user, organization_id)
    try:
        return service.get_session(organization_id, session_id)
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post(
    "/sessions/{session_id}/start",
    response_model=SessionResponse,
    summary="Start Multi-Agent Session",
)
async def start_session(
    session_id: int,
    organization_id: int = Query(...),
    current_user: User = Depends(RequirePermission(_PERM_WRITE)),
    service: MultiAgentService = Depends(get_multi_agent_service),
) -> Any:
    """Transition a PENDING session to RUNNING and fanout sub-tasks."""
    _assert_org(current_user, organization_id)
    try:
        return await service.start_session(organization_id, session_id)
    except Exception as exc:
        raise _handle_domain_error(exc)


@router.post(
    "/sessions/{session_id}/complete",
    response_model=SessionResponse,
    summary="Complete Multi-Agent Session",
)
async def complete_session(
    session_id: int,
    organization_id: int = Query(...),
    current_user: User = Depends(RequirePermission(_PERM_WRITE)),
    service: MultiAgentService = Depends(get_multi_agent_service),
) -> Any:
    """Collect agent results, merge them and mark the session COMPLETED."""
    _assert_org(current_user, organization_id)
    try:
        return await service.complete_session(organization_id, session_id)
    except Exception as exc:
        raise _handle_domain_error(exc)


@router.post(
    "/sessions/{session_id}/cancel",
    response_model=SessionResponse,
    summary="Cancel Multi-Agent Session",
)
def cancel_session(
    session_id: int,
    organization_id: int = Query(...),
    current_user: User = Depends(RequirePermission(_PERM_WRITE)),
    service: MultiAgentService = Depends(get_multi_agent_service),
) -> Any:
    """Cancel a collaboration session."""
    _assert_org(current_user, organization_id)
    try:
        return service.cancel_session(organization_id, session_id)
    except Exception as exc:
        raise _handle_domain_error(exc)


# ────────────────────────────────────────────────────────────────────────────
# Shared context
# ────────────────────────────────────────────────────────────────────────────

@router.patch(
    "/sessions/{session_id}/context",
    response_model=SessionResponse,
    summary="Update Shared Context",
)
def update_context(
    session_id: int,
    payload: UpdateContext,
    organization_id: int = Query(...),
    current_user: User = Depends(RequirePermission(_PERM_WRITE)),
    service: MultiAgentService = Depends(get_multi_agent_service),
) -> Any:
    """Merge partial updates into the session's shared context."""
    _assert_org(current_user, organization_id)
    try:
        return service.update_shared_context(organization_id, session_id, payload.updates)
    except Exception as exc:
        raise _handle_domain_error(exc)


# ────────────────────────────────────────────────────────────────────────────
# Delegation
# ────────────────────────────────────────────────────────────────────────────

@router.post(
    "/sessions/{session_id}/delegate",
    response_model=AgentDelegationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Delegate Task",
)
def delegate_task(
    session_id: int,
    payload: DelegateTask,
    organization_id: int = Query(...),
    current_user: User = Depends(RequirePermission(_PERM_WRITE)),
    service: MultiAgentService = Depends(get_multi_agent_service),
) -> Any:
    """Delegate a task from one agent to another within the session."""
    _assert_org(current_user, organization_id)
    try:
        return service.delegate_task(
            organization_id=organization_id,
            session_id=session_id,
            from_agent_id=payload.from_agent_id,
            to_agent_id=payload.to_agent_id,
            task_description=payload.task_description,
            context=payload.context,
        )
    except Exception as exc:
        raise _handle_domain_error(exc)


@router.get(
    "/sessions/{session_id}/delegations",
    response_model=list[AgentDelegationResponse],
    summary="List Delegations",
)
def list_delegations(
    session_id: int,
    organization_id: int = Query(...),
    current_user: User = Depends(RequirePermission(_PERM_READ)),
    service: MultiAgentService = Depends(get_multi_agent_service),
) -> Any:
    """List all task delegations in a session."""
    _assert_org(current_user, organization_id)
    try:
        return service.list_delegations(organization_id, session_id)
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.patch(
    "/sessions/{session_id}/delegations/{delegation_id}",
    response_model=AgentDelegationResponse,
    summary="Resolve Delegation",
)
def resolve_delegation(
    session_id: int,
    delegation_id: int,
    delegation_status: str = Query(..., alias="status", description="COMPLETED | FAILED | ACCEPTED"),
    result: dict[str, Any] | None = None,
    organization_id: int = Query(...),
    current_user: User = Depends(RequirePermission(_PERM_WRITE)),
    service: MultiAgentService = Depends(get_multi_agent_service),
) -> Any:
    """Mark a delegation as resolved (COMPLETED, FAILED, or ACCEPTED)."""
    _assert_org(current_user, organization_id)
    try:
        return service.resolve_delegation(
            organization_id=organization_id,
            session_id=session_id,
            delegation_id=delegation_id,
            status=delegation_status,
            result=result,
        )
    except Exception as exc:
        raise _handle_domain_error(exc)


# ────────────────────────────────────────────────────────────────────────────
# Messaging
# ────────────────────────────────────────────────────────────────────────────

@router.post(
    "/sessions/{session_id}/messages",
    response_model=AgentInterMessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send Inter-Agent Message",
)
async def send_message(
    session_id: int,
    payload: SendMessage,
    organization_id: int = Query(...),
    current_user: User = Depends(RequirePermission(_PERM_WRITE)),
    service: MultiAgentService = Depends(get_multi_agent_service),
) -> Any:
    """Publish a message from one agent to another (or broadcast)."""
    _assert_org(current_user, organization_id)
    try:
        return await service.send_message(
            organization_id=organization_id,
            session_id=session_id,
            from_agent_id=payload.from_agent_id,
            to_agent_id=payload.to_agent_id,
            message_type=payload.message_type,
            content=payload.content,
        )
    except Exception as exc:
        raise _handle_domain_error(exc)


@router.get(
    "/sessions/{session_id}/messages",
    response_model=list[AgentInterMessageResponse],
    summary="List Inter-Agent Messages",
)
def list_messages(
    session_id: int,
    organization_id: int = Query(...),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    current_user: User = Depends(RequirePermission(_PERM_READ)),
    service: MultiAgentService = Depends(get_multi_agent_service),
) -> Any:
    """List all persisted inter-agent messages in a session."""
    _assert_org(current_user, organization_id)
    try:
        return service.list_messages(organization_id, session_id, offset, limit)
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


# ────────────────────────────────────────────────────────────────────────────
# Participant status
# ────────────────────────────────────────────────────────────────────────────

@router.patch(
    "/sessions/{session_id}/participants/{agent_id}/status",
    response_model=ParticipantResponse,
    summary="Update Participant Status",
)
def update_participant_status(
    session_id: int,
    agent_id: int,
    payload: UpdateParticipantStatus,
    organization_id: int = Query(...),
    current_user: User = Depends(RequirePermission(_PERM_WRITE)),
    service: MultiAgentService = Depends(get_multi_agent_service),
) -> Any:
    """Update the execution status and optional result for a session participant."""
    _assert_org(current_user, organization_id)
    try:
        return service.update_participant_status(
            organization_id=organization_id,
            session_id=session_id,
            agent_id=agent_id,
            status=payload.status,
            result=payload.result,
        )
    except Exception as exc:
        raise _handle_domain_error(exc)
