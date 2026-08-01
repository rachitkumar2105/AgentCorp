"""
Tool Calling Engine — Tool Registry.

The Registry is the single source of truth for all callable tool functions.
It maps tool names (strings, matching the Tool.name in the database) to
Python callables (sync or async).

Responsibilities:
  - Register tools (static, programmatic, future: dynamic/plugin/remote)
  - Unregister tools
  - Resolve a callable by name
  - Expose ToolMetadata for each registered tool (used by the Serializer)
  - Cache metadata lookups

The Registry NEVER executes tools — that is exclusively the Executor's job.
The Registry NEVER validates permissions — that is the Validator's job.

Extension points (no redesign needed):
  - Dynamic registration:  tools can call ``registry.register()`` at runtime.
  - Plugin registration:   a plugin loader discovers tools from entry_points.
  - Remote/MCP tools:      an adapter registers a proxy callable that calls
                           the remote endpoint via HTTP/MCP protocol.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable, Coroutine
from typing import Any

from app.schemas.tool_execution import ToolMetadata, ToolParameter, ToolSchema
from app.tools.exceptions import ToolNotFoundError

logger = logging.getLogger("tool_registry")

# Type alias: a tool function may be sync or async
ToolCallable = Callable[..., Any] | Callable[..., Coroutine[Any, Any, Any]]


class ToolEntry:
    """
    Internal registry entry binding a ToolMetadata to its callable.

    Not exposed outside the registry — callers only receive ToolMetadata.
    """

    __slots__ = ("metadata", "fn", "is_async")

    def __init__(self, metadata: ToolMetadata, fn: ToolCallable) -> None:
        self.metadata = metadata
        self.fn = fn
        self.is_async = asyncio.iscoroutinefunction(fn)


class ToolRegistry:
    """
    Central registry for all tool callables.

    Thread-safe for read access.  Writes (register/unregister) should
    happen at startup or within a lock in a concurrent context.

    Usage::

        @tool_registry.tool(
            name="search_web",
            description="Search the web for a given query.",
            parameters=ToolSchema(
                properties={"query": ToolParameter(type="string", description="Search term")},
                required=["query"],
            ),
        )
        async def search_web(query: str) -> str:
            ...

    Or imperatively::

        tool_registry.register(metadata, callable_fn)
    """

    def __init__(self) -> None:
        self._entries: dict[str, ToolEntry] = {}

    # ------------------------------------------------------------------
    # Registration API
    # ------------------------------------------------------------------

    def register(
        self,
        metadata: ToolMetadata,
        fn: ToolCallable,
    ) -> None:
        """
        Register a tool callable.

        Args:
            metadata: Full ToolMetadata for this tool.
            fn:       The Python callable (sync or async).

        Raises:
            ValueError if a tool with the same name is already registered.
        """
        if metadata.name in self._entries:
            logger.warning(
                "tool_registry | duplicate registration | tool=%s — overwriting",
                metadata.name,
            )
        self._entries[metadata.name] = ToolEntry(metadata=metadata, fn=fn)
        logger.info("tool_registry | registered | tool=%s version=%s", metadata.name, metadata.version)

    def unregister(self, tool_name: str) -> None:
        """
        Remove a tool from the registry.

        Silently ignores names that are not registered.
        """
        removed = self._entries.pop(tool_name, None)
        if removed:
            logger.info("tool_registry | unregistered | tool=%s", tool_name)

    def tool(
        self,
        *,
        name: str,
        description: str,
        parameters: ToolSchema | None = None,
        version: str = "1.0.0",
        timeout_seconds: float = 30.0,
        max_retries: int = 1,
        category: str | None = None,
        tags: list[str] | None = None,
        # db_id is 0 for built-in tools; real IDs are set by the engine
        # when it discovers tools from the database.
        db_id: int = 0,
    ) -> Callable[[ToolCallable], ToolCallable]:
        """
        Decorator for registering a Python function as a tool.

        Example::

            @tool_registry.tool(
                name="get_current_time",
                description="Returns the current UTC time as an ISO 8601 string.",
            )
            async def get_current_time() -> str:
                from datetime import datetime, timezone
                return datetime.now(timezone.utc).isoformat()
        """
        def decorator(fn: ToolCallable) -> ToolCallable:
            meta = ToolMetadata(
                id=db_id,
                name=name,
                description=description,
                parameters=parameters or ToolSchema(properties={}, required=[]),
                version=version,
                timeout_seconds=timeout_seconds,
                max_retries=max_retries,
                category=category,
                tags=tags or [],
            )
            self.register(meta, fn)
            return fn
        return decorator

    # ------------------------------------------------------------------
    # Lookup API
    # ------------------------------------------------------------------

    def get_metadata(self, tool_name: str) -> ToolMetadata:
        """
        Return metadata for a registered tool.

        Raises:
            ToolNotFoundError if the tool is not registered.
        """
        entry = self._entries.get(tool_name)
        if entry is None:
            raise ToolNotFoundError(
                f"Tool '{tool_name}' is not registered in the Tool Registry.",
                tool_name=tool_name,
            )
        return entry.metadata

    def get_callable(self, tool_name: str) -> ToolEntry:
        """
        Return the internal ToolEntry (metadata + callable) for a tool.

        Raises:
            ToolNotFoundError if the tool is not registered.
        """
        entry = self._entries.get(tool_name)
        if entry is None:
            raise ToolNotFoundError(
                f"Tool '{tool_name}' is not registered in the Tool Registry.",
                tool_name=tool_name,
            )
        return entry

    def list_all(self) -> list[ToolMetadata]:
        """Return metadata for all registered tools (enabled or not)."""
        return [e.metadata for e in self._entries.values()]

    def list_enabled(self) -> list[ToolMetadata]:
        """Return metadata for all currently enabled tools."""
        return [e.metadata for e in self._entries.values() if e.metadata.enabled]

    def is_registered(self, tool_name: str) -> bool:
        """Return True if the tool name is registered."""
        return tool_name in self._entries

    def count(self) -> int:
        """Return the number of registered tools."""
        return len(self._entries)

    # ------------------------------------------------------------------
    # Database synchronisation
    # ------------------------------------------------------------------

    def sync_db_id(self, tool_name: str, db_id: int) -> None:
        """
        Update the ``id`` field on a registered tool after database discovery.

        Called by the ToolExecutionService when it loads tools from the DB
        to align in-registry metadata with persisted IDs.
        """
        entry = self._entries.get(tool_name)
        if entry:
            # ToolMetadata is a Pydantic model — use model_copy for immutability
            entry.metadata = entry.metadata.model_copy(update={"id": db_id})

    def set_enabled(self, tool_name: str, *, enabled: bool) -> None:
        """
        Enable or disable a tool at runtime without unregistering it.
        """
        entry = self._entries.get(tool_name)
        if entry:
            entry.metadata = entry.metadata.model_copy(update={"enabled": enabled})


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

tool_registry = ToolRegistry()


# ---------------------------------------------------------------------------
# Built-in utility tools (always available — override in production as needed)
# ---------------------------------------------------------------------------


@tool_registry.tool(
    name="get_current_time",
    description=(
        "Returns the current UTC date and time as an ISO 8601 string. "
        "Use this tool when the user asks about the current time or date."
    ),
    category="utility",
    tags=["time", "date", "utility"],
)
async def _builtin_get_current_time() -> str:
    """Return current UTC time."""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


@tool_registry.tool(
    name="echo",
    description=(
        "Echoes the input message back unchanged. "
        "Useful for testing tool calling pipelines without external dependencies."
    ),
    parameters=ToolSchema(
        properties={
            "message": ToolParameter(
                type="string",
                description="The message to echo back.",
                max_length=1000,
            )
        },
        required=["message"],
    ),
    category="utility",
    tags=["debug", "test", "utility"],
)
async def _builtin_echo(message: str) -> str:
    """Echo a message."""
    return message
