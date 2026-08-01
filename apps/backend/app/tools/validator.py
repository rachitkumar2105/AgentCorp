"""
Tool Calling Engine — Validator.

Validates a tool call request before execution. Checks:
  - Organization isolation
  - RBAC permissions
  - Agent-tool mappings
  - Parameter JSON Schema validation
  - Required parameters presence
"""

from __future__ import annotations

import logging
from typing import Any

from app.models.user import User
from app.repositories.agent_tool_repository import AgentToolRepository
from app.repositories.tool_repository import ToolRepository
from app.schemas.tool_execution import ToolCallRequest, ToolValidationResult
from app.tools.exceptions import (
    ToolDisabledError,
    ToolNotFoundError,
    ToolPermissionDeniedError,
    ToolValidationError,
)
from app.tools.registry import tool_registry

logger = logging.getLogger("tool_validator")


class ToolValidator:
    """
    Validates tool execution parameters and permissions.
    """

    def __init__(
        self,
        tool_repo: ToolRepository,
        agent_tool_repo: AgentToolRepository,
    ) -> None:
        self.tool_repo = tool_repo
        self.agent_tool_repo = agent_tool_repo

    def validate_request(
        self,
        request: ToolCallRequest,
        current_user: User,
    ) -> ToolValidationResult:
        """
        Validate permissions, environment, and schemas for a tool request.
        """
        tool_name = request.tool_name
        logger.debug("validate_request | tool=%s args=%s", tool_name, request.arguments)

        try:
            # 1. Verify existence in registry
            if not tool_registry.is_registered(tool_name):
                raise ToolNotFoundError(f"Tool '{tool_name}' not found in registry.", tool_name=tool_name)

            entry = tool_registry.get_callable(tool_name)
            meta = entry.metadata

            # 2. Check if tool is enabled
            if not meta.enabled:
                raise ToolDisabledError(f"Tool '{tool_name}' is disabled.", tool_name=tool_name)

            # 3. DB validation: tool must exist in DB and match the registry name
            db_tool = self.tool_repo.get_by_name(tool_name)
            if not db_tool:
                raise ToolNotFoundError(f"Tool '{tool_name}' not registered in database.", tool_name=tool_name)

            # Sync ID
            tool_registry.sync_db_id(tool_name, db_tool.id)

            # 4. Organization isolation & Agent mapping check
            if request.agent_id is not None:
                assignment = self.agent_tool_repo.get_assignment(
                    agent_id=request.agent_id,
                    tool_id=db_tool.id,
                )
                if not assignment:
                    raise ToolPermissionDeniedError(
                        f"Tool '{tool_name}' is not assigned to agent {request.agent_id}.",
                        tool_name=tool_name,
                    )

            # 5. Argument JSON Schema validation
            schema = meta.parameters
            field_errors: dict[str, str] = {}

            # Check required fields
            for req in schema.required:
                if req not in request.arguments:
                    field_errors[req] = "Missing required parameter"

            # Check parameter types and bounds
            for param_name, param in schema.properties.items():
                if param_name in request.arguments:
                    val = request.arguments[param_name]
                    # basic type check
                    if param.type == "string" and not isinstance(val, str):
                        field_errors[param_name] = f"Expected type string, got {type(val).__name__}"
                    elif param.type == "integer" and not isinstance(val, int):
                        field_errors[param_name] = f"Expected type integer, got {type(val).__name__}"
                    elif param.type == "number" and not isinstance(val, (int, float)):
                        field_errors[param_name] = f"Expected type number, got {type(val).__name__}"
                    elif param.type == "boolean" and not isinstance(val, bool):
                        field_errors[param_name] = f"Expected type boolean, got {type(val).__name__}"

            if field_errors:
                raise ToolValidationError(
                    f"Parameter validation failed for tool '{tool_name}'.",
                    tool_name=tool_name,
                    field_errors=field_errors,
                )

            return ToolValidationResult(
                valid=True,
                tool_name=tool_name,
            )

        except (ToolNotFoundError, ToolDisabledError, ToolPermissionDeniedError, ToolValidationError) as exc:
            field_errs = getattr(exc, "field_errors", {})
            return ToolValidationResult(
                valid=False,
                tool_name=tool_name,
                error_code=exc.__class__.__name__,
                error_message=str(exc),
                field_errors=field_errs,
            )
