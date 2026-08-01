"""
Provider schemas for all AI providers.

These schemas define the common request/response contracts used by
the provider layer. Every provider (Groq, OpenAI, Gemini, Anthropic,
OpenRouter, Ollama, etc.) must translate its native API into these
schemas so the rest of the application remains provider-agnostic.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ChatMessage(BaseModel):
    """Represents a single chat message."""

    model_config = ConfigDict(extra="forbid")

    role: MessageRole
    content: str
    name: str | None = None
    tool_call_id: str | None = None


class ToolParameter(BaseModel):
    """Single tool parameter."""

    model_config = ConfigDict(extra="forbid")

    type: str
    description: str | None = None
    enum: list[str] | None = None


class ToolDefinition(BaseModel):
    """Provider-independent tool definition."""

    model_config = ConfigDict(extra="forbid")

    name: str
    description: str

    parameters: dict[str, ToolParameter] = Field(default_factory=dict)

    required: list[str] = Field(default_factory=list)


class ToolCall(BaseModel):
    """Tool requested by the model."""

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    arguments: dict[str, Any]


class ToolResult(BaseModel):
    """Result returned from executed tool."""

    model_config = ConfigDict(extra="forbid")

    tool_call_id: str
    content: str


class ChatRequest(BaseModel):
    """Normalized chat request."""

    model_config = ConfigDict(extra="forbid")

    model: str

    messages: list[ChatMessage]

    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
    )

    max_tokens: int | None = Field(
        default=None,
        gt=0,
    )

    top_p: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    stream: bool = False

    tools: list[ToolDefinition] = Field(default_factory=list)

    tool_choice: str | None = None

    stop: list[str] | None = None


class Usage(BaseModel):
    """Token usage."""

    model_config = ConfigDict(extra="forbid")

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatResponse(BaseModel):
    """Normalized provider response."""

    model_config = ConfigDict(extra="forbid")

    model: str

    message: ChatMessage

    finish_reason: str | None = None

    usage: Usage | None = None

    tool_calls: list[ToolCall] = Field(default_factory=list)


class EmbeddingRequest(BaseModel):
    """Embedding request."""

    model_config = ConfigDict(extra="forbid")

    model: str

    input: str | list[str]


class EmbeddingVector(BaseModel):
    """Single embedding vector."""

    model_config = ConfigDict(extra="forbid")

    embedding: list[float]

    index: int


class EmbeddingResponse(BaseModel):
    """Embedding response."""

    model_config = ConfigDict(extra="forbid")

    model: str

    data: list[EmbeddingVector]


class StreamChunk(BaseModel):
    """
    Single token / delta chunk yielded by a streaming provider.

    Providers yield a sequence of StreamChunk objects via an async generator.
    The Streaming Engine accumulates these and forwards each to the client as
    a Server-Sent Event immediately upon arrival.

    Fields:
        token        : The text fragment (may be empty for the final chunk).
        index        : Zero-based ordinal of this chunk in the stream.
        finish_reason: Set on the last chunk; None for all intermediate ones.
        usage        : Populated only on the final chunk (or None if not reported).
        model        : Model that generated this chunk.
    """

    model_config = ConfigDict(extra="forbid")

    token: str = ""
    index: int = 0
    finish_reason: str | None = None
    usage: Usage | None = None
    model: str = ""