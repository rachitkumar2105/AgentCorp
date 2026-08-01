"""
SSE (Server-Sent Events) utility helpers.

Provides a thin, standard-compliant SSE formatting layer that can be
consumed by any async generator producing ``StreamChunk`` objects.

Design goals:
  - Zero coupling to any specific provider
  - WebSocket-ready: the ``format_sse`` helper is transport-agnostic;
    only the caller decides how to deliver the bytes
  - Standard SSE format (RFC 8895) — no custom protocols
  - Extensible event types for future tool calls, citations, memory, etc.

Standard SSE wire format used throughout AgentCorp:

    event: token
    data: {"token":"Hello","index":0,"provider":"groq","model":"llama3"}

    event: done
    data: {"finish_reason":"stop","usage":{...},"latency":0.42}

    event: error
    data: {"error":"Provider timeout","code":"provider_timeout"}
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


# ---------------------------------------------------------------------------
# SSE event type constants
# ---------------------------------------------------------------------------

SSE_EVENT_TOKEN = "token"
SSE_EVENT_DONE = "done"
SSE_EVENT_ERROR = "error"
SSE_EVENT_PING = "ping"


# ---------------------------------------------------------------------------
# Wire format helpers
# ---------------------------------------------------------------------------


def format_sse(event: str, data: Any) -> str:
    """
    Format a single Server-Sent Event as a correctly encoded string.

    Follows RFC 8895:
        event: <event_name>\\n
        data: <json_payload>\\n
        \\n

    Args:
        event: SSE event name (e.g. ``"token"``, ``"done"``, ``"error"``).
        data:  JSON-serialisable payload.  If already a string it is used
               as-is; otherwise it is serialised with ``json.dumps``.

    Returns:
        A string ready to be written directly to an SSE response stream.
    """
    if isinstance(data, str):
        serialised = data
    else:
        serialised = json.dumps(data, ensure_ascii=False, default=str)

    return f"event: {event}\ndata: {serialised}\n\n"


def format_token_event(
    token: str,
    index: int,
    provider: str,
    model: str,
) -> str:
    """
    Format a ``token`` SSE event from raw chunk fields.

    Timestamps are included so that clients can measure inter-token latency
    and detect stalled streams without implementing their own timers.
    """
    payload = {
        "token": token,
        "index": index,
        "provider": provider,
        "model": model,
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    return format_sse(SSE_EVENT_TOKEN, payload)


def format_done_event(
    finish_reason: str,
    usage: dict[str, int] | None,
    latency: float,
    tokens_sent: int,
) -> str:
    """
    Format the terminal ``done`` SSE event.

    Args:
        finish_reason: Why the model stopped (``"stop"``, ``"length"``, etc.).
        usage:         Token usage dict with ``prompt_tokens``, etc.  May be None.
        latency:       Wall-clock seconds from first token to stream end.
        tokens_sent:   Total number of token chunks forwarded to the client.
    """
    payload: dict[str, Any] = {
        "finish_reason": finish_reason,
        "latency": round(latency, 4),
        "tokens_sent": tokens_sent,
    }
    if usage:
        payload["usage"] = usage
    return format_sse(SSE_EVENT_DONE, payload)


def format_error_event(error: str, code: str = "streaming_error") -> str:
    """
    Format an ``error`` SSE event.

    Args:
        error: Human-readable error description (never includes raw API keys).
        code:  Machine-readable error code for client-side handling.
    """
    payload = {
        "error": error,
        "code": code,
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    return format_sse(SSE_EVENT_ERROR, payload)


def format_ping_event() -> str:
    """
    Format a ``ping`` SSE event to keep the connection alive.

    Should be sent every ~15 s when the provider is slow to produce tokens.
    """
    return format_sse(SSE_EVENT_PING, {"ts": datetime.now(timezone.utc).isoformat()})


# ---------------------------------------------------------------------------
# Stream metrics tracker
# ---------------------------------------------------------------------------


@dataclass
class StreamMetrics:
    """
    Tracks per-stream metrics during an active SSE session.

    Thread-safe for single-coroutine use (one stream = one coroutine).
    Global counters (active/completed/cancelled/failed) are module-level
    so that a future Prometheus integration can read them without coupling
    to any particular request.
    """

    conversation_id: int
    organization_id: int
    provider: str
    model: str

    start_time: float = field(default_factory=time.perf_counter)
    tokens_sent: int = 0
    finish_reason: str = ""
    completed: bool = False
    cancelled: bool = False
    failed: bool = False

    def record_token(self) -> None:
        """Increment the token counter."""
        self.tokens_sent += 1

    def elapsed(self) -> float:
        """Seconds since stream start."""
        return time.perf_counter() - self.start_time

    def tokens_per_second(self) -> float:
        """Current throughput in tokens/s."""
        elapsed = self.elapsed()
        return self.tokens_sent / elapsed if elapsed > 0 else 0.0


# ---------------------------------------------------------------------------
# Global in-process counters (lightweight; replace with Prometheus later)
# ---------------------------------------------------------------------------

_active_streams: int = 0
_completed_streams: int = 0
_cancelled_streams: int = 0
_failed_streams: int = 0
_total_latency: float = 0.0
_total_tokens: int = 0


def increment_active() -> None:
    global _active_streams
    _active_streams += 1


def decrement_active() -> None:
    global _active_streams
    _active_streams = max(0, _active_streams - 1)


def record_completed(latency: float, tokens: int) -> None:
    global _completed_streams, _total_latency, _total_tokens
    _completed_streams += 1
    _total_latency += latency
    _total_tokens += tokens


def record_cancelled() -> None:
    global _cancelled_streams
    _cancelled_streams += 1


def record_failed() -> None:
    global _failed_streams
    _failed_streams += 1


def get_metrics_snapshot() -> dict[str, Any]:
    """Return a snapshot of global stream metrics (for health/admin endpoints)."""
    avg_latency = _total_latency / _completed_streams if _completed_streams else 0.0
    avg_tps = _total_tokens / _total_latency if _total_latency > 0 else 0.0
    return {
        "active_streams": _active_streams,
        "completed_streams": _completed_streams,
        "cancelled_streams": _cancelled_streams,
        "failed_streams": _failed_streams,
        "average_latency_seconds": round(avg_latency, 4),
        "average_tokens_per_second": round(avg_tps, 2),
    }
