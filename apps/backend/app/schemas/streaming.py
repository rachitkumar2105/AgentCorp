"""
Streaming Engine Pydantic v2 schemas.

Defines the request and event schemas used by:
  - REST endpoints  (app/api/v1/streaming.py)
  - Streaming Service (app/services/streaming_service.py)
  - Future WebSocket transport (reuses the same models)

All schemas are deliberately transport-agnostic so that a WebSocket
layer can reuse them without modification.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class StreamingChatRequest(BaseModel):
    """
    Incoming request for a streaming chat session.

    ``conversation_id`` is required for continuation streams.
    ``agent_id`` is required when creating a new conversation stream.
    """

    model_config = ConfigDict(extra="forbid")

    agent_id: Optional[int] = Field(
        None,
        description="Agent ID — required when creating a new conversation (POST /chat/stream)",
    )
    conversation_id: Optional[int] = Field(
        None,
        description="Existing conversation ID — required for continuation streams",
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=32_768,
        description="User message to deliver to the agent",
    )
    provider: Optional[str] = Field(
        None,
        description="Override provider name. Orchestrator decides when omitted.",
    )
    model: Optional[str] = Field(
        None,
        description="Override model name. Agent default used when omitted.",
    )
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0)
    max_tokens: Optional[int] = Field(None, gt=0)
    runtime_version: str = Field("AgentCorp V1")

    # Future-compatibility placeholders
    tool_choice: Optional[str] = Field(
        None,
        description="Reserved for Tool Calling module",
    )


# ---------------------------------------------------------------------------
# SSE event payload schemas
# (not sent over the wire as Pydantic models — serialised manually for speed)
# ---------------------------------------------------------------------------


class StreamingToken(BaseModel):
    """
    Payload for each ``token`` SSE event.

    Includes ordering metadata so that clients can detect dropped events
    and reconstruct the correct sequence even if events arrive out of order
    (unlikely with SSE, but future WebSocket transport may reorder).
    """

    model_config = ConfigDict(extra="forbid")

    token: str = Field(..., description="Text fragment from the model")
    index: int = Field(..., description="Zero-based position of this token in the stream")
    provider: str = Field(..., description="Provider that emitted this token")
    model: str = Field(..., description="Model that emitted this token")
    ts: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of token emission",
    )


class StreamingUsage(BaseModel):
    """Token usage reported in the ``done`` event."""

    model_config = ConfigDict(extra="forbid")

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class StreamingCompleted(BaseModel):
    """
    Payload for the terminal ``done`` SSE event.

    Carries all provenance data needed for billing, audit, and UI display.
    """

    model_config = ConfigDict(extra="forbid")

    conversation_id: int
    message_id: int = Field(..., description="DB ID of the persisted assistant message")
    finish_reason: str = Field(..., description="Why generation stopped")
    usage: Optional[StreamingUsage] = None
    latency: float = Field(..., description="Wall-clock seconds from start to last token")
    tokens_sent: int = Field(..., description="Number of token SSE events forwarded")
    provider: str
    model: str


class StreamingError(BaseModel):
    """
    Payload for an ``error`` SSE event.

    Clients should display an appropriate error message and allow the user
    to retry.  ``code`` enables programmatic handling.
    """

    model_config = ConfigDict(extra="forbid")

    error: str = Field(..., description="Human-readable error description")
    code: str = Field(
        ...,
        description=(
            "Machine-readable error code, e.g. "
            "'provider_timeout', 'provider_unavailable', 'permission_denied'"
        ),
    )
    conversation_id: Optional[int] = None
