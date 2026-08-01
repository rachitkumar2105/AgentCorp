"""
Agent Engine — v1 REST endpoints.
"""

from __future__ import annotations

import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies.auth import get_current_active_user
from app.dependencies.permissions import RequirePermission
from app.dependencies.agent_engine import get_agent_engine_service
from app.models.user import User
from app.schemas.agent_engine import GoalCreate, GoalResponse, AgentExecutionResponse
from app.services.agent_engine_service import AgentEngineService

logger = logging.getLogger("agent_engine_api")

router = APIRouter(
    prefix="/api/v1/agent",
    tags=["Agent Engine"],
)

_PERM_AGENT_WRITE = "agent:write"
_PERM_AGENT_READ = "agent:read"


@router.post(
    "/goals",
    response_model=GoalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Goal",
)
def create_goal(
    payload: GoalCreate,
    organization_id: int = Query(..., description="ID of scoping organization"),
    current_user: User = Depends(RequirePermission(_PERM_AGENT_WRITE)),
    service: AgentEngineService = Depends(get_agent_engine_service),
) -> GoalResponse:
    """Create a new goal definition objective and decompose subtasks."""
    _assert_org_membership(current_user, organization_id)
    return service.create_goal(
        name=payload.title,
        description=payload.description,
        objective=payload.objective,
        priority=payload.priority,
        success_criteria=payload.success_criteria,
        organization_id=organization_id,
        agent_id=payload.agent_id,
        conversation_id=payload.conversation_id,
        user_id=current_user.id,
    )


@router.post(
    "/goals/{goal_id}/execute",
    response_model=AgentExecutionResponse,
    summary="Execute Goal",
)
async def execute_goal(
    goal_id: int,
    organization_id: int = Query(..., description="ID of scoping organization"),
    current_user: User = Depends(RequirePermission(_PERM_AGENT_WRITE)),
    service: AgentEngineService = Depends(get_agent_engine_service),
) -> AgentExecutionResponse:
    """Validate and run execution loops for a goal objective."""
    _assert_org_membership(current_user, organization_id)
    try:
        execution = await service.execute_goal(
            goal_id=goal_id,
            organization_id=organization_id,
            current_user=current_user,
        )
        return execution
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post(
    "/executions/{execution_id}/pause",
    response_model=AgentExecutionResponse,
    summary="Pause Execution",
)
def pause_execution(
    execution_id: int,
    organization_id: int = Query(..., description="ID of scoping organization"),
    current_user: User = Depends(RequirePermission(_PERM_AGENT_WRITE)),
    service: AgentEngineService = Depends(get_agent_engine_service),
) -> AgentExecutionResponse:
    """Pause execution state of a running agent loop."""
    _assert_org_membership(current_user, organization_id)
    try:
        return service.pause_execution(organization_id, execution_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post(
    "/executions/{execution_id}/resume",
    response_model=AgentExecutionResponse,
    summary="Resume Execution",
)
def resume_execution(
    execution_id: int,
    organization_id: int = Query(..., description="ID of scoping organization"),
    current_user: User = Depends(RequirePermission(_PERM_AGENT_WRITE)),
    service: AgentEngineService = Depends(get_agent_engine_service),
) -> AgentExecutionResponse:
    """Resume execution state of a paused agent loop."""
    _assert_org_membership(current_user, organization_id)
    try:
        return service.resume_execution(organization_id, execution_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post(
    "/executions/{execution_id}/cancel",
    response_model=AgentExecutionResponse,
    summary="Cancel Execution",
)
def cancel_execution(
    execution_id: int,
    organization_id: int = Query(..., description="ID of scoping organization"),
    current_user: User = Depends(RequirePermission(_PERM_AGENT_WRITE)),
    service: AgentEngineService = Depends(get_agent_engine_service),
) -> AgentExecutionResponse:
    """Cancel execution state of a running agent loop."""
    _assert_org_membership(current_user, organization_id)
    try:
        return service.cancel_execution(organization_id, execution_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get(
    "/executions/{execution_id}",
    response_model=AgentExecutionResponse,
    summary="Execution Status",
)
def get_execution_status(
    execution_id: int,
    organization_id: int = Query(..., description="ID of scoping organization"),
    current_user: User = Depends(RequirePermission(_PERM_AGENT_READ)),
    service: AgentEngineService = Depends(get_agent_engine_service),
) -> AgentExecutionResponse:
    """Retrieve details on a specific execution run."""
    _assert_org_membership(current_user, organization_id)
    execution = service.get_execution(organization_id, execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found.")
    return execution


@router.get(
    "/goals/{goal_id}",
    response_model=GoalResponse,
    summary="Goal Details",
)
def get_goal_details(
    goal_id: int,
    organization_id: int = Query(..., description="ID of scoping organization"),
    current_user: User = Depends(RequirePermission(_PERM_AGENT_READ)),
    service: AgentEngineService = Depends(get_agent_engine_service),
) -> GoalResponse:
    """Retrieve details on a specific goal objective."""
    _assert_org_membership(current_user, organization_id)
    goal = service.get_goal(organization_id, goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found.")
    return goal


def _assert_org_membership(user: User, organization_id: int) -> None:
    if user.is_superuser:
        return
    member_org_ids = {m.organization_id for m in user.organizations}
    if organization_id not in member_org_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of the specified organization.",
        )
