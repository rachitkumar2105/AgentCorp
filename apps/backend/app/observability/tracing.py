"""
Tracing abstraction module supporting parent-child spans and correlation IDs.
"""

import time
import uuid
from contextvars import ContextVar
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from app.observability.logging import correlation_id_ctx, get_logger

logger = get_logger(__name__)

# Active trace span variable context
active_span_ctx: ContextVar[Optional["Span"]] = ContextVar("active_span", default=None)


class Span:
    """Represents a single timing and metadata context in a trace tree."""

    def __init__(
        self,
        name: str,
        tracer: "Tracer",
        parent: Optional["Span"] = None,
        correlation_id: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None,
    ):
        self.name = name
        self.tracer = tracer
        self.parent = parent
        self.span_id = str(uuid.uuid4())
        self.trace_id = parent.trace_id if parent else str(uuid.uuid4())
        self.correlation_id = correlation_id or correlation_id_ctx.get() or self.trace_id
        
        self.start_time = time.perf_counter()
        self.start_timestamp = datetime.now(timezone.utc).isoformat()
        self.end_time: Optional[float] = None
        self.end_timestamp: Optional[str] = None
        self.duration: Optional[float] = None
        self.tags = tags or {}
        self.children: List["Span"] = []
        self._token = None

    def add_tag(self, key: str, value: Any) -> None:
        """Add metadata tag to the span."""
        self.tags[key] = value

    def finish(self) -> None:
        """Close the span, compute duration, and trigger export/publish."""
        self.end_time = time.perf_counter()
        self.end_timestamp = datetime.now(timezone.utc).isoformat()
        self.duration = self.end_time - self.start_time
        
        # Reset context variable token
        if self._token:
            active_span_ctx.reset(self._token)
            self._token = None

        # Notify tracer
        self.tracer.span_finished(self)

    def __enter__(self) -> "Span":
        self._token = active_span_ctx.set(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type:
            self.add_tag("error", True)
            self.add_tag("error.message", str(exc_val))
            self.add_tag("error.type", exc_type.__name__)
        self.finish()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize span details."""
        return {
            "name": self.name,
            "span_id": self.span_id,
            "trace_id": self.trace_id,
            "parent_id": self.parent.span_id if self.parent else None,
            "correlation_id": self.correlation_id,
            "start_time": self.start_timestamp,
            "end_time": self.end_timestamp,
            "duration": self.duration,
            "tags": self.tags,
        }


class Tracer:
    """Tracer registry for managing and storing trace trees."""

    def __init__(self):
        self.finished_spans: List[Dict[str, Any]] = []

    def start_span(self, name: str, tags: Optional[Dict[str, Any]] = None) -> Span:
        """Start a new span within the active context."""
        parent = active_span_ctx.get()
        span = Span(name=name, tracer=self, parent=parent, tags=tags)
        if parent:
            parent.children.append(span)
        return span

    def span_finished(self, span: Span) -> None:
        """Hook triggered when a span finishes."""
        serialized = span.to_dict()
        self.finished_spans.append(serialized)
        
        # Log slow operations if threshold exceeded
        if span.duration and span.duration > 1.0:
            logger.warning(
                "Slow operation detected: %s took %.4fs (correlation_id=%s)",
                span.name,
                span.duration,
                span.correlation_id,
            )


# Global tracer instance
tracer = Tracer()
