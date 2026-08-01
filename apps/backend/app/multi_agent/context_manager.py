"""
Multi-Agent Collaboration System — Shared Context Manager.

Maintains a thread-safe, session-scoped shared context dict that all agents
within a session can read and update.  The canonical state is always the
JSON column in the database; this in-process cache reduces DB round-trips
for hot paths.
"""

from __future__ import annotations

import logging
from typing import Any

from app.multi_agent.exceptions import ContextSyncError

logger = logging.getLogger("multi_agent.context")


class SharedContextManager:
    """
    In-process cache of a session's shared context, with merge helpers.

    Callers must flush the merged context back to the DB after mutation.
    """

    def __init__(self, initial_context: dict[str, Any] | None = None) -> None:
        self._context: dict[str, Any] = initial_context or {}

    # ------------------------------------------------------------------ #
    # Read helpers                                                          #
    # ------------------------------------------------------------------ #

    def get(self, key: str, default: Any = None) -> Any:
        """Return the value for *key* from the shared context."""
        return self._context.get(key, default)

    def snapshot(self) -> dict[str, Any]:
        """Return a shallow copy of the current shared context."""
        return dict(self._context)

    # ------------------------------------------------------------------ #
    # Write helpers                                                         #
    # ------------------------------------------------------------------ #

    def merge(self, updates: dict[str, Any]) -> None:
        """
        Merge *updates* into the shared context using a shallow-merge strategy.

        Top-level dict values are merged recursively (one level deep); all
        other types are overwritten.
        """
        for key, value in updates.items():
            if (
                isinstance(value, dict)
                and isinstance(self._context.get(key), dict)
            ):
                self._context[key] = {**self._context[key], **value}
            else:
                self._context[key] = value

    def set(self, key: str, value: Any) -> None:
        """Set a single key in the shared context."""
        self._context[key] = value

    def delete(self, key: str) -> None:
        """Remove a key from the shared context."""
        self._context.pop(key, None)

    def replace(self, new_context: dict[str, Any]) -> None:
        """
        Fully replace the in-memory context, e.g. after a DB reload.
        Raises *ContextSyncError* if *new_context* is not a dict.
        """
        if not isinstance(new_context, dict):
            raise ContextSyncError("Shared context must be a dict.")
        self._context = new_context
