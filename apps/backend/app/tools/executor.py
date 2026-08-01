"""
Tool Calling Engine — Executor.

Directly runs a tool function within the sandbox. Handles:
  - Synchronous and asynchronous callable execution
  - Timeout and cancellation enforcement via Sandbox
  - Structured error catching and retry limits
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from app.schemas.tool_execution import ToolCallRequest, ToolCallResult
from app.tools.exceptions import (
    ToolExecutionError,
    ToolExecutionFailedError,
    ToolValidationError,
)
from app.tools.registry import tool_registry
from app.tools.sandbox import tool_sandbox

logger = logging.getLogger("tool_executor")


class ToolExecutor:
    """
    Executes tool call tasks inside the logical sandbox.
    """

    async def execute(
        self,
        request: ToolCallRequest,
    ) -> ToolCallResult:
        """
        Execute a single tool call request using sandbox safeguards.
        """
        tool_name = request.tool_name
        start_time = time.perf_counter()

        # Resolve registry entry
        entry = tool_registry.get_callable(tool_name)
        meta = entry.metadata
        max_retries = meta.max_retries
        timeout_seconds = meta.timeout_seconds

        retries_used = 0
        success = False
        content = ""
        error_code = None

        while True:
            try:
                # 1. Sandbox checks on arguments
                tool_sandbox.check_argument_payload_size(request.arguments, tool_name)
                tool_sandbox.check_argument_nesting_depth(request.arguments, tool_name)

                # 2. Run callable function inside sandbox timeout wrapper
                if entry.is_async:
                    coro = entry.fn(**request.arguments)
                    raw_result = await tool_sandbox.execute_with_timeout(
                        coro=coro,
                        tool_name=tool_name,
                        timeout_seconds=timeout_seconds,
                    )
                else:
                    # Run sync in threadpool to avoid blocking main loop
                    loop = asyncio.get_running_loop()
                    raw_result = await loop.run_in_executor(
                        None,
                        lambda: entry.fn(**request.arguments),
                    )

                # 3. Format and sanitize result
                if isinstance(raw_result, str):
                    content = raw_result
                else:
                    content = json_dump_safe(raw_result)

                # Sandbox check on output size
                tool_sandbox.check_result_payload_size(content, tool_name)
                success = True
                break

            except Exception as exc:
                latency = time.perf_counter() - start_time
                # Handle retries if the failure is retryable
                is_retryable = False
                if isinstance(exc, ToolExecutionError) and exc.retryable:
                    is_retryable = True

                # Non-engine exceptions are wrapped as failed execution
                if not isinstance(exc, ToolExecutionError):
                    exc = ToolExecutionFailedError(
                        message=f"Tool execution failed: {exc}",
                        tool_name=tool_name,
                        cause=exc,
                        retryable=True, # Transient by default unless specific validation failure
                    )
                    is_retryable = True

                if is_retryable and retries_used < max_retries:
                    retries_used += 1
                    logger.warning(
                        "tool_executor | retrying | tool=%s attempt=%d/%d latency=%.4fs error=%s",
                        tool_name,
                        retries_used,
                        max_retries,
                        latency,
                        exc,
                    )
                    # Small backoff before retry
                    await asyncio.sleep(0.5 * retries_used)
                    continue

                # Max retries exceeded or non-retryable error
                success = False
                error_code = exc.__class__.__name__
                content = str(exc)
                logger.error(
                    "tool_executor | failed | tool=%s retries=%d latency=%.4fs error=%s",
                    tool_name,
                    retries_used,
                    latency,
                    exc,
                )
                break

        latency = time.perf_counter() - start_time
        return ToolCallResult(
            call_id=request.call_id,
            tool_name=tool_name,
            success=success,
            content=content,
            error_code=error_code,
            latency_seconds=latency,
            retries_used=retries_used,
        )


def json_dump_safe(val: Any) -> str:
    """Safe JSON string dumper."""
    import json
    try:
        return json.dumps(val, ensure_ascii=False)
    except Exception:
        return str(val)
