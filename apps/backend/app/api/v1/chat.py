"""
Chat Engine REST API — v1 endpoints.

Exposes the following routes:

  POST /api/v1/chat                              → create new conversation + first assistant message
  POST /api/v1/chat/{conversation_id}            → continue existing conversation
  POST /api/v1/chat/{conversation_id}/regenerate → regenerate last assistant message
  POST /api/v1/chat/{conversation_id}/retry      → retry failed AI execution
  GET  /api/v1/chat/{conversation_id}            → retrieve conversation with paginated history

All business logic lives in ChatService.
RBAC is enforced via RequirePermission.
Organisation isolation is enforced inside ChatService.

Organisation resolution:
  The caller must supply ``organization_id`` as a query parameter.
  This supports multi-org users and is the cleanest REST approach.
  Future: move to an ``X-Organization-ID`` header via a dedicated dependency.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies.auth import get_current_active_user
from app.dependencies.chat import get_chat_service
from app.dependencies.runtime import get_runtime_router
from app.dependencies.permissions import RequirePermission
from app.models.user import User
from app.schemas.chat import (
    ChatCreateRequest,
    ChatContinueRequest,
    ChatRegenerateRequest,
    ChatResponseSchema,
    ChatRetryRequest,
    ConversationDetailSchema,
)
from app.runtime.router import RuntimeRouter
from app.services.chat_service import ChatService

logger = logging.getLogger("chat_api")

router = APIRouter(
    prefix="/api/v1/chat",
    tags=["Chat Engine"],
)

# ---------------------------------------------------------------------------
# RBAC permission constants
# ---------------------------------------------------------------------------
_PERM_CHAT = "chat:send"
_PERM_CHAT_READ = "chat:read"


# ---------------------------------------------------------------------------
# POST /api/v1/chat — create a new conversation
# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=ChatResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create Chat Response",
    description=(
        "Creates a new conversation and returns the first assistant message. "
        "Requires the ``chat:send`` permission. "
        "``agent_id`` in the request body identifies which agent handles this conversation."
    ),
)
async def create_chat(
    payload: ChatCreateRequest,
    organization_id: int = Query(..., description="ID of the organisation scoping this request"),
    current_user: User = Depends(RequirePermission(_PERM_CHAT)),
    runtime_router: RuntimeRouter = Depends(get_runtime_router),
) -> ChatResponseSchema:
    """
    Create a brand-new conversation and generate the first assistant response.

    ``provider`` and ``model`` overrides are optional; the AI Orchestrator
    resolves them via agent defaults and automatic failover when omitted.
    """
    _assert_org_membership(current_user, organization_id)
    logger.info(
        "create_chat | user_id=%s org_id=%s agent_id=%s",
        current_user.id,
        organization_id,
        payload.agent_id,
    )
    return await runtime_router.execute_chat(
        payload=payload,
        current_user=current_user,
        organization_id=organization_id,
        runtime_version=payload.runtime_version,
    )


# ---------------------------------------------------------------------------
# POST /api/v1/chat/{conversation_id} — continue conversation
# ---------------------------------------------------------------------------


@router.post(
    "/{conversation_id}",
    response_model=ChatResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Continue Conversation",
    description=(
        "Appends a new user message to an existing conversation and returns "
        "the next assistant response."
    ),
)
async def continue_chat(
    conversation_id: int,
    payload: ChatContinueRequest,
    organization_id: int = Query(..., description="ID of the organisation scoping this request"),
    current_user: User = Depends(RequirePermission(_PERM_CHAT)),
    runtime_router: RuntimeRouter = Depends(get_runtime_router),
) -> ChatResponseSchema:
    """
    Continue an existing conversation with a new user message.

    Validates organisation ownership and user access before executing.
    """
    _assert_org_membership(current_user, organization_id)
    logger.info(
        "continue_chat | user_id=%s org_id=%s conv_id=%s",
        current_user.id,
        organization_id,
        conversation_id,
    )
    return await runtime_router.execute_chat(
        payload=payload,
        conversation_id=conversation_id,
        current_user=current_user,
        organization_id=organization_id,
        runtime_version=payload.runtime_version,
    )


# ---------------------------------------------------------------------------
# POST /api/v1/chat/{conversation_id}/regenerate — regenerate last response
# ---------------------------------------------------------------------------


@router.post(
    "/{conversation_id}/regenerate",
    response_model=ChatResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Regenerate Response",
    description=(
        "Generates a NEW assistant message without re-sending a user message. "
        "Conversation history is preserved; compatible with future branching."
    ),
)
async def regenerate_response(
    conversation_id: int,
    payload: ChatRegenerateRequest,
    organization_id: int = Query(..., description="ID of the organisation scoping this request"),
    current_user: User = Depends(RequirePermission(_PERM_CHAT)),
    runtime_router: RuntimeRouter = Depends(get_runtime_router),
) -> ChatResponseSchema:
    """
    Create a new assistant message for the last user turn.

    Nothing is deleted — a fresh response is appended to the conversation.
    """
    _assert_org_membership(current_user, organization_id)
    logger.info(
        "regenerate_response | user_id=%s org_id=%s conv_id=%s",
        current_user.id,
        organization_id,
        conversation_id,
    )
    return await runtime_router.execute_chat(
        payload=payload,
        conversation_id=conversation_id,
        current_user=current_user,
        organization_id=organization_id,
        runtime_version=payload.runtime_version,
    )


# ---------------------------------------------------------------------------
# POST /api/v1/chat/{conversation_id}/retry — retry failed execution
# ---------------------------------------------------------------------------


@router.post(
    "/{conversation_id}/retry",
    response_model=ChatResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Retry Failed Message",
    description=(
        "Re-executes the AI Orchestrator for the last failed assistant message. "
        "No duplicate user messages are created."
    ),
)
async def retry_failed_message(
    conversation_id: int,
    payload: ChatRetryRequest,
    organization_id: int = Query(..., description="ID of the organisation scoping this request"),
    current_user: User = Depends(RequirePermission(_PERM_CHAT)),
    runtime_router: RuntimeRouter = Depends(get_runtime_router),
) -> ChatResponseSchema:
    """
    Retry provider execution for the last failed assistant response.

    Provider and model overrides are accepted for manual failover.
    """
    _assert_org_membership(current_user, organization_id)
    logger.info(
        "retry_failed_message | user_id=%s org_id=%s conv_id=%s",
        current_user.id,
        organization_id,
        conversation_id,
    )
    return await runtime_router.execute_chat(
        payload=payload,
        conversation_id=conversation_id,
        current_user=current_user,
        organization_id=organization_id,
        runtime_version=payload.runtime_version,
    )


# ---------------------------------------------------------------------------
# GET /api/v1/chat/{conversation_id} — retrieve conversation
# ---------------------------------------------------------------------------


@router.get(
    "/{conversation_id}",
    response_model=ConversationDetailSchema,
    status_code=status.HTTP_200_OK,
    summary="Conversation Summary",
    description=(
        "Returns conversation metadata and a paginated message history. "
        "Supports ``page`` and ``page_size`` query parameters."
    ),
)
def get_conversation(
    conversation_id: int,
    organization_id: int = Query(..., description="ID of the organisation scoping this request"),
    page: int = Query(default=1, ge=1, description="1-based page number"),
    page_size: int = Query(default=20, ge=1, le=200, description="Messages per page"),
    current_user: User = Depends(RequirePermission(_PERM_CHAT_READ)),
    chat_service: ChatService = Depends(get_chat_service),
) -> ConversationDetailSchema:
    """
    Retrieve a conversation with paginated message history.

    Access is restricted to the conversation owner and superusers.
    """
    _assert_org_membership(current_user, organization_id)
    logger.info(
        "get_conversation | user_id=%s org_id=%s conv_id=%s page=%s page_size=%s",
        current_user.id,
        organization_id,
        conversation_id,
        page,
        page_size,
    )
    return chat_service.get_conversation(
        conversation_id=conversation_id,
        current_user=current_user,
        organization_id=organization_id,
        page=page,
        page_size=page_size,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _assert_org_membership(user: User, organization_id: int) -> None:
    """
    Verify that the authenticated user is a member of the requested organisation.

    Superusers bypass this check.
    Raises HTTP 403 if the user does not belong to the organisation.
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
