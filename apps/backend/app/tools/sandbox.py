"""
Tool Calling Engine — Execution Sandbox.

Provides a centralised abstraction for all execution safeguards applied
before and during tool execution.  Today's safeguards are logical
(timeout, payload size, recursion depth).  Future safeguards
(CPU/memory limits, containerised execution, network isolation) can be
added here without changing the Executor or Dispatcher.

Design:
  - Sandbox is stateless — instantiate once per engine startup.
  - Constraints are enforced at the boundary between the Dispatcher
    and the Executor; neither knows about the other's internals.
  - All async — never blocks the event loop.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Callable, Coroutine

from app.tools.exceptions import (
    ToolExecutionCancelledError,
    ToolExecutionTimeoutError,
    ToolRecursionLimitExceededError,
    ToolValidationError,
)

logger = logging.getLogger("tool_sandbox")

# ---------------------------------------------------------------------------
# Configurable defaults
# ---------------------------------------------------------------------------

DEFAULT_TIMEOUT_SECONDS: float = 30.0
MAX_TIMEOUT_SECONDS: float = 120.0
MAX_PAYLOAD_BYTES: int = 256 * 1024      # 256 KB
MAX_RESULT_BYTES: int = 512 * 1024       # 512 KB
MAX_RECURSION_DEPTH: int = 5
MAX_ARGUMENTS_DEPTH: int = 5             # JSON nesting depth in arguments


class ToolSandbox:
    """
    Execution safeguards for the Tool Calling Engine.

    Responsibilities:
      - Enforce per-tool timeout via asyncio.wait_for
      - Validate argument payload size
      - Validate result payload size
      - Enforce recursion depth limit
      - Validate argument JSON nesting depth
      - Support graceful cancellation

    Future extensions (no redesign needed):
      - CPU/memory limit via resource module or cgroup
      - Containerised execution via subprocess/Docker
      - Network policy enforcement
      - Secrets scrubbing before persistence
    """

    def __init__(
        self,
        max_recursion_depth: int = MAX_RECURSION_DEPTH,
        max_payload_bytes: int = MAX_PAYLOAD_BYTES,
        max_result_bytes: int = MAX_RESULT_BYTES,
        default_timeout: float = DEFAULT_TIMEOUT_SECONDS,
        max_timeout: float = MAX_TIMEOUT_SECONDS,
    ) -> None:
        self._max_recursion_depth = max_recursion_depth
        self._max_payload_bytes = max_payload_bytes
        self._max_result_bytes = max_result_bytes
        self._default_timeout = default_timeout
        self._max_timeout = max_timeout

    # ------------------------------------------------------------------
    # Pre-execution guards
    # ------------------------------------------------------------------

    def check_recursion_depth(
        self,
        depth: int,
        tool_name: str,
    ) -> None:
        """
        Raise ToolRecursionLimitExceededError if the call depth is too high.

        Args:
            depth:     Current depth (0 for top-level calls).
            tool_name: Name of the tool being invoked.
        """
        if depth > self._max_recursion_depth:
            logger.warning(
                "tool_sandbox | recursion limit exceeded | tool=%s depth=%d limit=%d",
                tool_name,
                depth,
                self._max_recursion_depth,
            )
            raise ToolRecursionLimitExceededError(
                f"Recursion limit of {self._max_recursion_depth} exceeded "
                f"at depth {depth} for tool '{tool_name}'.",
                tool_name=tool_name,
                depth=depth,
            )

    def check_argument_payload_size(
        self,
        arguments: dict,
        tool_name: str,
    ) -> None:
        """
        Raise ToolValidationError if the serialised argument payload is too large.
        """
        try:
            size = len(json.dumps(arguments).encode("utf-8"))
        except (TypeError, ValueError) as exc:
            raise ToolValidationError(
                f"Arguments for tool '{tool_name}' are not JSON-serialisable: {exc}",
                tool_name=tool_name,
            )

        if size > self._max_payload_bytes:
            raise ToolValidationError(
                f"Arguments payload for tool '{tool_name}' is {size} bytes "
                f"(limit {self._max_payload_bytes} bytes).",
                tool_name=tool_name,
            )

    def check_argument_nesting_depth(
        self,
        arguments: dict,
        tool_name: str,
    ) -> None:
        """
        Raise ToolValidationError if JSON argument nesting is too deep.

        Prevents stack overflow attacks via deeply nested JSON.
        """
        def _depth(obj: Any, current: int = 0) -> int:
            if current > MAX_ARGUMENTS_DEPTH:
                return current
            if isinstance(obj, dict):
                if not obj:
                    return current
                return max(_depth(v, current + 1) for v in obj.values())
            if isinstance(obj, list):
                if not obj:
                    return current
                return max(_depth(v, current + 1) for v in obj)
            return current

        d = _depth(arguments)
        if d > MAX_ARGUMENTS_DEPTH:
            raise ToolValidationError(
                f"Arguments for tool '{tool_name}' have nesting depth {d} "
                f"(limit {MAX_ARGUMENTS_DEPTH}).",
                tool_name=tool_name,
            )

    # ------------------------------------------------------------------
    # Execution wrapper
    # ------------------------------------------------------------------

    async def execute_with_timeout(
        self,
        coro: Coroutine[Any, Any, Any],
        tool_name: str,
        timeout_seconds: float | None = None,
    ) -> Any:
        """
        Run ``coro`` with a timeout and clean cancellation handling.

        Args:
            coro           : The tool's coroutine to execute.
            tool_name      : Used in log and exception messages.
            timeout_seconds: Per-call override.  Clamped to MAX_TIMEOUT_SECONDS.
                             Falls back to DEFAULT_TIMEOUT_SECONDS when None.

        Returns:
            Whatever the coroutine returns.

        Raises:
            ToolExecutionTimeoutError   : Timeout expired.
            ToolExecutionCancelledError : Task was cancelled externally.
        """
        timeout = min(
            timeout_seconds if timeout_seconds is not None else self._default_timeout,
            self._max_timeout,
        )

        try:
            return await asyncio.wait_for(coro, timeout=timeout)

        except asyncio.TimeoutError:
            logger.warning(
                "tool_sandbox | timeout | tool=%s timeout=%.2fs",
                tool_name,
                timeout,
            )
            raise ToolExecutionTimeoutError(
                f"Tool '{tool_name}' exceeded timeout of {timeout:.1f}s.",
                tool_name=tool_name,
            )

        except asyncio.CancelledError:
            logger.info(
                "tool_sandbox | cancelled | tool=%s",
                tool_name,
            )
            raise ToolExecutionCancelledError(
                f"Tool '{tool_name}' was cancelled.",
                tool_name=tool_name,
            )

    # ------------------------------------------------------------------
    # Post-execution guards
    # ------------------------------------------------------------------

    def check_result_payload_size(
        self,
        result_content: str,
        tool_name: str,
    ) -> None:
        """
        Raise ToolValidationError if the result string exceeds the size limit.

        Protects against the LLM context being flooded by excessively large
        tool results (e.g. a tool that returns an entire database dump).
        """
        size = len(result_content.encode("utf-8"))
        if size > self._max_result_bytes:
            logger.warning(
                "tool_sandbox | result too large | tool=%s size=%d limit=%d",
                tool_name,
                size,
                self._max_result_bytes,
            )
            raise ToolValidationError(
                f"Result from tool '{tool_name}' is {size} bytes "
                f"(limit {self._max_result_bytes} bytes). "
                "Consider paginating or summarising the tool output.",
                tool_name=tool_name,
            )


# Module-level singleton — shared across all requests
tool_sandbox = ToolSandbox()
