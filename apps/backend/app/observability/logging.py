"""
Structured JSON logging module with contextvars support.
"""

import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Dict

# Context variables for tracing/request metadata
request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)
correlation_id_ctx: ContextVar[str | None] = ContextVar("correlation_id", default=None)
organization_id_ctx: ContextVar[int | None] = ContextVar("organization_id", default=None)
user_id_ctx: ContextVar[int | None] = ContextVar("user_id", default=None)
agent_id_ctx: ContextVar[int | None] = ContextVar("agent_id", default=None)
conversation_id_ctx: ContextVar[int | None] = ContextVar("conversation_id", default=None)
execution_id_ctx: ContextVar[str | None] = ContextVar("execution_id", default=None)

# Service and module identifier
SERVICE_NAME = "agentcorp-backend"


def get_logging_context() -> Dict[str, Any]:
    """Retrieve all active values in contextvars."""
    return {
        "request_id": request_id_ctx.get(),
        "correlation_id": correlation_id_ctx.get(),
        "organization_id": organization_id_ctx.get(),
        "user_id": user_id_ctx.get(),
        "agent_id": agent_id_ctx.get(),
        "conversation_id": conversation_id_ctx.get(),
        "execution_id": execution_id_ctx.get(),
    }


def set_logging_context(
    request_id: str | None = None,
    correlation_id: str | None = None,
    organization_id: int | None = None,
    user_id: int | None = None,
    agent_id: int | None = None,
    conversation_id: int | None = None,
    execution_id: str | None = None,
) -> None:
    """Set the logging context variables."""
    if request_id is not None:
        request_id_ctx.set(request_id)
    if correlation_id is not None:
        correlation_id_ctx.set(correlation_id)
    if organization_id is not None:
        organization_id_ctx.set(organization_id)
    if user_id is not None:
        user_id_ctx.set(user_id)
    if agent_id is not None:
        agent_id_ctx.set(agent_id)
    if conversation_id is not None:
        conversation_id_ctx.set(conversation_id)
    if execution_id is not None:
        execution_id_ctx.set(execution_id)


def clear_logging_context() -> None:
    """Clear all logging context variables."""
    request_id_ctx.set(None)
    correlation_id_ctx.set(None)
    organization_id_ctx.set(None)
    user_id_ctx.set(None)
    agent_id_ctx.set(None)
    conversation_id_ctx.set(None)
    execution_id_ctx.set(None)


class JSONFormatter(logging.Formatter):
    """
    Formatter that outputs JSON logs containing standard fields plus request context.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "log_level": record.levelname,
            "service": SERVICE_NAME,
            "module": record.name,
            "message": record.getMessage(),
        }

        # Inject context variables
        log_data.update(get_logging_context())

        # If extra dictionary passed to log, add it
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        # Include exception info if any
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


class StructuredLogger(logging.Logger):
    """
    Custom logger that supports passing arbitrary extra dict to structured logs.
    """

    def _log(self, level: int, msg: Any, args: Any, exc_info: Any = None, extra: Any = None, stack_info: bool = False, stacklevel: int = 1) -> None:
        if extra and isinstance(extra, dict):
            # Extract fields that are not in the standard extra arguments
            extra_fields = {k: v for k, v in extra.items() if k not in ("request_id", "correlation_id", "organization_id", "user_id")}
            # Create a clean record modification
            def make_record_decorator(record):
                record.extra_fields = extra_fields
                return record
        super()._log(level, msg, args, exc_info=exc_info, extra=extra, stack_info=stack_info, stacklevel=stacklevel)


def setup_structured_logging(sink: str = "stdout", log_file: str | None = None) -> None:
    """
    Configures the root logger to use JSON formatting.
    """
    # Set our custom logger class
    logging.setLoggerClass(StructuredLogger)

    root = logging.getLogger()
    root.setLevel(logging.INFO)

    # Clean existing handlers
    for handler in list(root.handlers):
        root.removeHandler(handler)

    formatter = JSONFormatter()

    # stdout handler
    if sink == "stdout":
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setFormatter(formatter)
        root.addHandler(stdout_handler)
    
    # file handler if configured
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """
    Get a structured logger with name.
    """
    return logging.getLogger(name)
