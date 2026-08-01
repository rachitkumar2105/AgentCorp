"""
Tool Calling Engine — Dispatcher.

Orchestrates the entire tool calling pipeline:
  - Validates request using Validator
  - Limits execution depth using Sandbox
  - Routes request to Executor
  - Returns structured result
"""

from __future__ import annotations

import logging
import time

from app.models.user import User
from app.schemas.tool_execution import ToolCallRequest, ToolCallResult
from app.tools.exceptions import ToolValidationError
from app.tools.executor import ToolExecutor
from app.tools.sandbox import tool_sandbox
from app.tools.validator import ToolValidator

logger = logging.getLogger("tool_dispatcher")


class ToolDispatcher:
    """
    Coordinates validator and executor to process a single tool call request.
    """

    def __init__(
        self,
        validator: ToolValidator,
        executor: ToolExecutor,
    ) -> None:
        self.validator = validator
        self.executor = executor

    async def dispatch(
        self,
        request: ToolCallRequest,
        current_user: User,
    ) -> ToolCallResult:
        """
        Validate, route, and execute a tool call.
        """
        tool_name = request.tool_name
        start_time = time.perf_counter()

        logger.info(
            "tool_dispatcher | dispatching | tool=%s call_id=%s depth=%d",
            tool_name,
            request.call_id,
            request.recursion_depth,
        )

        try:
            # 1. Enforce recursion limit
            tool_sandbox.check_recursion_depth(request.recursion_depth, tool_name)

            # 2. Run validator
            validation = self.validator.validate_request(request, current_user)
            if not validation.valid:
                logger.warning(
                    "tool_dispatcher | validation failed | tool=%s error=%s",
                    tool_name,
                    validation.error_message,
                )
                return ToolCallResult(
                    call_id=request.call_id,
                    tool_name=tool_name,
                    success=False,
                    content=validation.error_message or "Validation failed.",
                    error_code=validation.error_code,
                    latency_seconds=time.perf_counter() - start_time,
                )

            # 3. Route to Executor
            result = await self.executor.execute(request)
            return result

        except Exception as exc:
            # Fallback error recovery
            logger.critical(
                "tool_dispatcher | unexpected error | tool=%s error=%s",
                tool_name,
                exc,
                exc_info=True,
            )
            return ToolCallResult(
                call_id=request.call_id,
                tool_name=tool_name,
                success=False,
                content=f"An unexpected dispatcher error occurred: {exc}",
                error_code=exc.__class__.__name__,
                latency_seconds=time.perf_counter() - start_time,
            )
