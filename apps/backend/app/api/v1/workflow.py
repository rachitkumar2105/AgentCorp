"""
Workflow Engine — v1 REST endpoints.
"""

from __future__ import annotations

import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies.auth import get_current_active_user
from app.dependencies.permissions import RequirePermission
from app.dependencies.workflow import get_workflow_service
from app.models.user import User
from app.schemas.workflow import WorkflowCreate, WorkflowResponse, ExecutionResponse
from app.services.workflow_service import WorkflowService

logger = logging.getLogger("workflow_api")

router = APIRouter(
    prefix="/api/v1/workflows",
    tags=["Workflow Engine"],
)

_PERM_WORKFLOW_WRITE = "workflow:write"
_PERM_WORKFLOW_READ = "workflow:read"


@router.post(
    "",
    response_model=WorkflowResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Workflow",
)
def create_workflow(
    payload: WorkflowCreate,
    organization_id: int = Query(..., description="ID of scoping organization"),
    current_user: User = Depends(RequirePermission(_PERM_WORKFLOW_WRITE)),
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowResponse:
    """Create a new logical workflow graph definition."""
    _assert_org_membership(current_user, organization_id)
    # Parse Pydantic payloads into dict lists
    nodes_list = [{"name": n.name, "node_type": n.node_type, "configuration": n.configuration, "timeout": n.timeout} for n in payload.nodes]
    edges_list = [{"source_node_index": e.source_node_id, "target_node_index": e.target_node_id, "transition_condition": e.transition_condition, "priority": e.priority} for e in payload.edges]

    return service.create_workflow(
        name=payload.name,
        description=payload.description,
        version=payload.version,
        organization_id=organization_id,
        user_id=current_user.id,
        nodes=nodes_list,
        edges=edges_list,
    )


@router.post(
    "/{workflow_id}/execute",
    response_model=ExecutionResponse,
    summary="Execute Workflow",
)
async def execute_workflow(
    workflow_id: int,
    organization_id: int = Query(..., description="ID of scoping organization"),
    agent_id: int = Query(..., description="Scoping agent for execution runs"),
    current_user: User = Depends(RequirePermission(_PERM_WORKFLOW_WRITE)),
    service: WorkflowService = Depends(get_workflow_service),
) -> ExecutionResponse:
    """Validate, initialize and run transition loops for a workflow."""
    _assert_org_membership(current_user, organization_id)
    try:
        execution = await service.execute_workflow(
            workflow_id=workflow_id,
            organization_id=organization_id,
            agent_id=agent_id,
            current_user=current_user,
        )
        return execution
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post(
    "/{execution_id}/pause",
    response_model=ExecutionResponse,
    summary="Pause Workflow",
)
def pause_workflow(
    execution_id: int,
    organization_id: int = Query(..., description="ID of scoping organization"),
    current_user: User = Depends(RequirePermission(_PERM_WORKFLOW_WRITE)),
    service: WorkflowService = Depends(get_workflow_service),
) -> ExecutionResponse:
    """Pause execution state of a running workflow."""
    _assert_org_membership(current_user, organization_id)
    try:
        return service.pause_execution(organization_id, execution_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post(
    "/{execution_id}/resume",
    response_model=ExecutionResponse,
    summary="Resume Workflow",
)
def resume_workflow(
    execution_id: int,
    organization_id: int = Query(..., description="ID of scoping organization"),
    current_user: User = Depends(RequirePermission(_PERM_WORKFLOW_WRITE)),
    service: WorkflowService = Depends(get_workflow_service),
) -> ExecutionResponse:
    """Resume execution state of a paused workflow."""
    _assert_org_membership(current_user, organization_id)
    try:
        return service.resume_execution(organization_id, execution_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post(
    "/{execution_id}/cancel",
    response_model=ExecutionResponse,
    summary="Cancel Workflow",
)
def cancel_workflow(
    execution_id: int,
    organization_id: int = Query(..., description="ID of scoping organization"),
    current_user: User = Depends(RequirePermission(_PERM_WORKFLOW_WRITE)),
    service: WorkflowService = Depends(get_workflow_service),
) -> ExecutionResponse:
    """Cancel execution state of a running workflow."""
    _assert_org_membership(current_user, organization_id)
    try:
        return service.cancel_execution(organization_id, execution_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get(
    "/{execution_id}",
    response_model=ExecutionResponse,
    summary="Execution Status",
)
def get_execution_status(
    execution_id: int,
    organization_id: int = Query(..., description="ID of scoping organization"),
    current_user: User = Depends(RequirePermission(_PERM_WORKFLOW_READ)),
    service: WorkflowService = Depends(get_workflow_service),
) -> ExecutionResponse:
    """Retrieve details on a specific execution run."""
    _assert_org_membership(current_user, organization_id)
    execution = service.get_execution(organization_id, execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found.")
    return execution


def _assert_org_membership(user: User, organization_id: int) -> None:
    if user.is_superuser:
        return
    member_org_ids = {m.organization_id for m in user.organizations}
    if organization_id not in member_org_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of the specified organization.",
        )
