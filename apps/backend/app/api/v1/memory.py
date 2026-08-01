"""
Memory Engine — v1 REST endpoints.
"""

from __future__ import annotations

import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies.auth import get_current_active_user
from app.dependencies.permissions import RequirePermission
from app.dependencies.memory import get_memory_service
from app.models.user import User
from app.schemas.memory import MemoryCreate, MemoryResponse, MemoryUpdate
from app.services.memory_service import MemoryService

logger = logging.getLogger("memory_api")

router = APIRouter(
    prefix="/api/v1/memory",
    tags=["Memory Engine"],
)

_PERM_MEM_WRITE = "memory:write"
_PERM_MEM_READ = "memory:read"


@router.post(
    "",
    response_model=MemoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Memory",
)
def create_memory(
    payload: MemoryCreate,
    organization_id: int = Query(..., description="ID of scoping organization"),
    current_user: User = Depends(RequirePermission(_PERM_MEM_WRITE)),
    service: MemoryService = Depends(get_memory_service),
) -> MemoryResponse:
    """Create a new memory manually or programmatically."""
    _assert_org_membership(current_user, organization_id)
    return service.create_memory(
        org_id=organization_id,
        agent_id=payload.agent_id,
        title=payload.title,
        content=payload.content,
        memory_type=payload.memory_type,
        importance_score=payload.importance_score,
        confidence_score=payload.confidence_score,
        user_id=current_user.id,
    )


@router.get(
    "",
    response_model=list[MemoryResponse],
    summary="List Memories",
)
def list_memories(
    organization_id: int = Query(..., description="ID of scoping organization"),
    agent_id: Optional[int] = Query(None, description="Filter by agent id"),
    memory_type: Optional[str] = Query(None, description="Filter by memory type"),
    current_user: User = Depends(RequirePermission(_PERM_MEM_READ)),
    service: MemoryService = Depends(get_memory_service),
) -> list[MemoryResponse]:
    """List active memories."""
    _assert_org_membership(current_user, organization_id)
    return service.list_memories(organization_id, agent_id, memory_type)


@router.get(
    "/{memory_id}",
    response_model=MemoryResponse,
    summary="Get Memory",
)
def get_memory(
    memory_id: int,
    organization_id: int = Query(..., description="ID of scoping organization"),
    current_user: User = Depends(RequirePermission(_PERM_MEM_READ)),
    service: MemoryService = Depends(get_memory_service),
) -> MemoryResponse:
    """Retrieve memory by ID."""
    _assert_org_membership(current_user, organization_id)
    try:
        return service.get_memory(organization_id, memory_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.put(
    "/{memory_id}",
    response_model=MemoryResponse,
    summary="Update Memory",
)
def update_memory(
    memory_id: int,
    payload: MemoryUpdate,
    organization_id: int = Query(..., description="ID of scoping organization"),
    current_user: User = Depends(RequirePermission(_PERM_MEM_WRITE)),
    service: MemoryService = Depends(get_memory_service),
) -> MemoryResponse:
    """Update memory fields."""
    _assert_org_membership(current_user, organization_id)
    try:
        return service.update_memory(
            org_id=organization_id,
            memory_id=memory_id,
            title=payload.title,
            content=payload.content,
            importance_score=payload.importance_score,
            confidence_score=payload.confidence_score,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post(
    "/{memory_id}/archive",
    response_model=MemoryResponse,
    summary="Archive Memory",
)
def archive_memory(
    memory_id: int,
    organization_id: int = Query(..., description="ID of scoping organization"),
    current_user: User = Depends(RequirePermission(_PERM_MEM_WRITE)),
    service: MemoryService = Depends(get_memory_service),
) -> MemoryResponse:
    """Archive memory instead of soft deleting."""
    _assert_org_membership(current_user, organization_id)
    try:
        return service.archive_memory(organization_id, memory_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete(
    "/{memory_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Memory",
)
def delete_memory(
    memory_id: int,
    organization_id: int = Query(..., description="ID of scoping organization"),
    current_user: User = Depends(RequirePermission(_PERM_MEM_WRITE)),
    service: MemoryService = Depends(get_memory_service),
) -> None:
    """Soft delete memory entry."""
    _assert_org_membership(current_user, organization_id)
    try:
        service.delete_memory(organization_id, memory_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# Auxiliary conversation summary endpoint to prevent path loops
summary_router = APIRouter(
    prefix="/api/v1/conversations",
    tags=["Memory Conversation Summary"],
)


@summary_router.post(
    "/{conversation_id}/summary",
    status_code=status.HTTP_200_OK,
    summary="Rebuild Conversation Summary",
)
def rebuild_conversation_summary(
    conversation_id: int,
    organization_id: int = Query(..., description="ID of scoping organization"),
    current_user: User = Depends(RequirePermission(_PERM_MEM_WRITE)),
    service: MemoryService = Depends(get_memory_service),
) -> dict:
    """Fetch message logs and build new summarized text metadata."""
    _assert_org_membership(current_user, organization_id)
    # Validate conversation belongs to organization (stub ownership check)
    conv = service.conv_repo.get(conversation_id)
    if not conv or conv.organization_id != organization_id:
         raise HTTPException(status_code=403, detail="Access denied.")

    summary = service.rebuild_summary(conversation_id)
    return {"conversation_id": conversation_id, "summary": summary}


def _assert_org_membership(user: User, organization_id: int) -> None:
    if user.is_superuser:
        return
    member_org_ids = {m.organization_id for m in user.organizations}
    if organization_id not in member_org_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of the specified organization.",
        )
