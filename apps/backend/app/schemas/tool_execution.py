"""
Tool Calling Engine — Pydantic v2 schemas.

These schemas are the single source of truth for every data contract in the
Tool Calling Engine.  They are provider-independent — no Groq, OpenAI, or
Gemini field names appear here.  Provider adapters translate between native
formats and these schemas via the Tool Serializer.

Future-compatible with:
  - Parallel tool execution    (batch field on ToolCallRequest)
  - Versioned tools            (version on ToolMetadata)
  - MCP remote tools           (endpoint on ToolMetadata)
  - Human-approval workflows   (approval_required on ToolMetadata)
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Tool metadata / schema models
# ---------------------------------------------------------------------------


class ToolParameter(BaseModel):
    """
    Schema for a single tool parameter.

    Mirrors the JSON Schema ``properties`` entry so that any serializer can
    convert this to the provider-specific parameter format without extra logic.
    """

    model_config = ConfigDict(extra="forbid")

    type: str = Field(..., description="JSON Schema type (string, integer, boolean, array, object)")
    description: Optional[str] = Field(None, description="Human-readable parameter description")
    enum: Optional[list[str]] = Field(None, description="Allowed values (if restricted set)")
    default: Optional[Any] = Field(None, description="Default value when parameter is omitted")
    items: Optional[dict[str, Any]] = Field(None, description="Schema for array items")
    minimum: Optional[float] = Field(None, description="Minimum numeric value")
    maximum: Optional[float] = Field(None, description="Maximum numeric value")
    min_length: Optional[int] = Field(None, description="Minimum string length")
    max_length: Optional[int] = Field(None, description="Maximum string length")


class ToolSchema(BaseModel):
    """
    Complete JSON Schema for a tool's input parameters.

    Equivalent to OpenAI's ``parameters`` object but expressed in our
    internal format so the serializer can produce any provider shape.
    """

    model_config = ConfigDict(extra="forbid")

    type: str = Field("object", description="Always 'object' for tool inputs")
    properties: dict[str, ToolParameter] = Field(default_factory=dict)
    required: list[str] = Field(default_factory=list)
    additional_properties: bool = Field(
        False,
        description="Whether extra keys are allowed — always False for safety",
    )


class ToolMetadata(BaseModel):
    """
    Complete metadata for a registered tool.

    This is the canonical representation used throughout the engine.
    Provider adapters convert FROM this TO provider-specific shapes.
    """

    model_config = ConfigDict(extra="forbid")

    id: int = Field(..., description="Database ID of the tool")
    name: str = Field(..., description="Unique tool name used as the function name in LLM calls")
    description: str = Field(..., description="Description shown to the LLM to guide tool selection")
    parameters: ToolSchema = Field(..., description="Input parameter schema")
    version: str = Field("1.0.0", description="Tool version — future support for versioned tools")
    timeout_seconds: float = Field(30.0, description="Per-execution timeout in seconds")
    max_retries: int = Field(1, description="Maximum retry attempts for transient failures")
    enabled: bool = Field(True, description="Whether the tool is currently active")
    category: Optional[str] = Field(None, description="Tool category for discovery / filtering")
    tags: list[str] = Field(default_factory=list, description="Discovery tags")
    approval_required: bool = Field(
        False,
        description="Reserved: require human approval before execution (future)",
    )
    endpoint: Optional[str] = Field(
        None,
        description="Reserved: remote MCP endpoint URL (future)",
    )


# ---------------------------------------------------------------------------
# Tool call request / result models
# ---------------------------------------------------------------------------


class ToolCallRequest(BaseModel):
    """
    A single tool call request emitted by the LLM.

    Created by the Tool Serializer from the provider-native tool call object.
    """

    model_config = ConfigDict(extra="forbid")

    call_id: str = Field(
        ...,
        description="Provider-assigned tool call ID — returned in the tool result message",
    )
    tool_name: str = Field(..., description="Name of the tool to invoke")
    arguments: dict[str, Any] = Field(
        default_factory=dict,
        description="Parsed JSON arguments from the LLM",
    )
    # Execution context (populated by the Dispatcher before execution)
    agent_id: Optional[int] = Field(None, description="Agent ID for permission checks")
    organization_id: Optional[int] = Field(None, description="Organisation ID for isolation")
    conversation_id: Optional[int] = Field(None, description="Conversation ID for audit trail")
    recursion_depth: int = Field(0, description="Current recursion depth — used by recursion guard")


class ToolCallResult(BaseModel):
    """
    Normalised result of a single tool invocation.

    Returned to the Dispatcher, then formatted into a ToolResult message
    by the Serializer and injected back into the conversation for the LLM.
    """

    model_config = ConfigDict(extra="forbid")

    call_id: str = Field(..., description="Echoed from ToolCallRequest.call_id")
    tool_name: str = Field(..., description="Echoed from ToolCallRequest.tool_name")
    success: bool = Field(..., description="True if execution completed without error")
    content: str = Field(
        ...,
        description=(
            "Serialised tool output (string for compatibility with all providers). "
            "On failure this contains a brief, safe error description."
        ),
    )
    error_code: Optional[str] = Field(
        None,
        description="Machine-readable error code when success=False",
    )
    latency_seconds: float = Field(0.0, description="Wall-clock execution time")
    retries_used: int = Field(0, description="Number of retry attempts consumed")


class ToolExecutionResult(BaseModel):
    """
    Aggregate result for a batch of tool calls in one LLM response.

    Wraps the list of individual ToolCallResult objects and adds
    per-batch metadata used for audit logging.
    """

    model_config = ConfigDict(extra="forbid")

    results: list[ToolCallResult] = Field(default_factory=list)
    total_latency_seconds: float = Field(0.0)
    all_succeeded: bool = Field(True)
    executed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


# ---------------------------------------------------------------------------
# Validation / audit models
# ---------------------------------------------------------------------------


class ToolValidationResult(BaseModel):
    """
    Outcome of the Tool Validator for a single ToolCallRequest.

    The Dispatcher checks ``valid`` before passing the call to the Executor.
    """

    model_config = ConfigDict(extra="forbid")

    valid: bool
    tool_name: str
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    field_errors: dict[str, str] = Field(default_factory=dict)


class ToolExecutionError(BaseModel):
    """
    Structured error payload included in ToolCallResult when success=False.

    This is the schema version — the exception hierarchy is in exceptions.py.
    """

    model_config = ConfigDict(extra="forbid")

    tool_name: str
    error_code: str
    message: str
    retryable: bool = False
