"""
Agent tool mapping API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies.auth import get_current_active_user
from app.dependencies.permissions import RequirePermission
from app.models.user import User
from app.schemas.agent_tool import AgentToolCreate, AgentToolResponse
from app.services.agent_tool_service import AgentToolService
from app.services.dependencies.tool import get_agent_tool_service

router = APIRouter(
    prefix="/agent-tools",
    tags=["Agent Tools"],
)


@router.post(
    "",
    response_model=AgentToolResponse,
    status_code=status.HTTP_201_CREATED,
)
def assign_tool(
    payload: AgentToolCreate,
    service: AgentToolService = Depends(get_agent_tool_service),
    current_user: User = Depends(RequirePermission("agent:update")),
):
    """
    Assign a tool to an agent.
    """
    try:
        return service.assign_tool(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.get(
    "/agent/{agent_id}",
    response_model=list[AgentToolResponse],
)
def list_agent_tools(
    agent_id: int,
    service: AgentToolService = Depends(get_agent_tool_service),
    current_user: User = Depends(get_current_active_user),
):
    """
    List all tools assigned to a specific agent.
    """
    return service.list_agent_tools(agent_id)


@router.delete(
    "/agent/{agent_id}/tool/{tool_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_tool(
    agent_id: int,
    tool_id: int,
    service: AgentToolService = Depends(get_agent_tool_service),
    current_user: User = Depends(RequirePermission("agent:update")),
):
    """
    Remove a tool assignment from an agent.
    """
    try:
        service.remove_tool(agent_id, tool_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
