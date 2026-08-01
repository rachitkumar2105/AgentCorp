"""
Tool Calling Engine — structured exceptions.

All exceptions are domain-specific and never expose Python stack traces
or raw provider errors to clients.  The Dispatcher catches these and
returns a ToolCallResult with the appropriate error information.

Hierarchy:
    ToolEngineError                      (base)
    ├── ToolNotFoundError
    ├── ToolDisabledError
    ├── ToolPermissionDeniedError
    ├── ToolValidationError
    ├── ToolExecutionError               (base for runtime failures)
    │   ├── ToolExecutionTimeoutError
    │   ├── ToolExecutionCancelledError
    │   ├── ToolExecutionFailedError
    │   └── ToolRecursionLimitExceededError
    └── ToolSerializationError
"""

from __future__ import annotations


class ToolEngineError(Exception):
    """Base exception for all Tool Calling Engine errors."""

    def __init__(self, message: str, *, tool_name: str | None = None) -> None:
        self.message = message
        self.tool_name = tool_name
        super().__init__(message)


class ToolNotFoundError(ToolEngineError):
    """
    Raised when the requested tool is not registered in the Tool Registry.

    This is a validation failure — the tool name was never registered,
    or was unregistered after the agent was configured.
    """


class ToolDisabledError(ToolEngineError):
    """
    Raised when the tool is registered but currently disabled or inactive.

    Do not retry — wait for the tool to be re-enabled.
    """


class ToolPermissionDeniedError(ToolEngineError):
    """
    Raised when RBAC or agent-level permission check fails.

    This is a hard validation failure — do not retry, do not log tool parameters.
    """


class ToolValidationError(ToolEngineError):
    """
    Raised when the input parameters fail schema, type, or required-field validation.

    ``field_errors`` maps field names to human-readable error descriptions.
    """

    def __init__(
        self,
        message: str,
        *,
        tool_name: str | None = None,
        field_errors: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message, tool_name=tool_name)
        self.field_errors: dict[str, str] = field_errors or {}


class ToolExecutionError(ToolEngineError):
    """
    Base class for all runtime execution failures.

    Unlike validation errors, execution errors may be retried if the
    failure is classified as transient.
    """

    def __init__(
        self,
        message: str,
        *,
        tool_name: str | None = None,
        retryable: bool = False,
    ) -> None:
        super().__init__(message, tool_name=tool_name)
        self.retryable = retryable


class ToolExecutionTimeoutError(ToolExecutionError):
    """
    Raised when a tool execution exceeds its configured timeout.

    Always considered retryable (the next attempt may succeed under
    lower system load), unless the timeout is fundamental to the tool design.
    """

    def __init__(self, message: str, *, tool_name: str | None = None) -> None:
        super().__init__(message, tool_name=tool_name, retryable=True)


class ToolExecutionCancelledError(ToolExecutionError):
    """
    Raised when execution is cancelled by the caller (e.g. client disconnect).

    Never retried — the stream session has ended.
    """

    def __init__(self, message: str, *, tool_name: str | None = None) -> None:
        super().__init__(message, tool_name=tool_name, retryable=False)


class ToolExecutionFailedError(ToolExecutionError):
    """
    Raised when the tool function raises an unexpected exception.

    ``cause`` holds the original exception (not forwarded to clients).
    """

    def __init__(
        self,
        message: str,
        *,
        tool_name: str | None = None,
        cause: Exception | None = None,
        retryable: bool = False,
    ) -> None:
        super().__init__(message, tool_name=tool_name, retryable=retryable)
        self.cause = cause


class ToolRecursionLimitExceededError(ToolExecutionError):
    """
    Raised when the tool calling recursion depth exceeds the configured limit.

    This is a safety guard against infinite Tool → AI → Tool loops.
    """

    def __init__(
        self,
        message: str,
        *,
        tool_name: str | None = None,
        depth: int = 0,
    ) -> None:
        super().__init__(message, tool_name=tool_name, retryable=False)
        self.depth = depth


class ToolSerializationError(ToolEngineError):
    """
    Raised when provider-format ↔ internal-format conversion fails.

    This is a programming error in a provider adapter, not a user error.
    """
