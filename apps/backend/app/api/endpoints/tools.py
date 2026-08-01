"""
Tool API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies.auth import get_current_active_user
from app.dependencies.permissions import RequirePermission
from app.models.user import User
from app.schemas.tool import ToolCreate, ToolResponse, ToolUpdate
from app.services.dependencies.tool import get_tool_service
from app.services.tool_service import ToolService

router = APIRouter(
    prefix="/tools",
    tags=["Tools"],
)


@router.post(
    "",
    response_model=ToolResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_tool(
    payload: ToolCreate,
    service: ToolService = Depends(get_tool_service),
    current_user: User = Depends(RequirePermission("tool:create")),
):
    """
    Create a new global tool.
    """
    try:
        return service.create(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.get(
    "",
    response_model=list[ToolResponse],
)
def list_tools(
    service: ToolService = Depends(get_tool_service),
    current_user: User = Depends(get_current_active_user),
):
    """
    List all global tools.
    """
    return service.list_all()


@router.get(
    "/{tool_id}",
    response_model=ToolResponse,
)
def get_tool(
    tool_id: int,
    service: ToolService = Depends(get_tool_service),
    current_user: User = Depends(get_current_active_user),
):
    """
    Retrieve a tool by ID.
    """
    tool = service.get(tool_id)
    if tool is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tool not found.",
        )
    return tool


@router.put(
    "/{tool_id}",
    response_model=ToolResponse,
)
def update_tool(
    tool_id: int,
    payload: ToolUpdate,
    service: ToolService = Depends(get_tool_service),
    current_user: User = Depends(RequirePermission("tool:update")),
):
    """
    Update a tool.
    """
    tool = service.get(tool_id)
    if tool is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tool not found.",
        )
    return service.update(tool, payload)


@router.delete(
    "/{tool_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_tool(
    tool_id: int,
    service: ToolService = Depends(get_tool_service),
    current_user: User = Depends(RequirePermission("tool:delete")),
):
    """
    Delete a tool.
    """
    tool = service.get(tool_id)
    if tool is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tool not found.",
        )
    service.delete(tool)
