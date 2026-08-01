"""
Multi-Agent Collaboration System — Message Bus.

Provides async pub-sub inter-agent messaging inside a collaboration session.
Messages are persisted to the database and optionally delivered in-memory for
real-time coordination.
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from typing import Callable, Awaitable

logger = logging.getLogger("multi_agent.message_bus")

# In-memory subscriber registry: session_id -> list[callbacks]
_subscribers: dict[int, list[Callable[[dict], Awaitable[None]]]] = defaultdict(list)


class MessageBus:
    """
    Lightweight async message bus for a Multi-Agent session.

    Agents subscribe to receive messages and publish events through this
    bus. All published messages are also expected to be persisted by the
    service layer; this class only handles in-process fanout.
    """

    def subscribe(self, session_id: int, callback: Callable[[dict], Awaitable[None]]) -> None:
        """Register *callback* to receive messages for *session_id*."""
        _subscribers[session_id].append(callback)
        logger.debug("Agent subscribed to session %d", session_id)

    def unsubscribe(self, session_id: int, callback: Callable[[dict], Awaitable[None]]) -> None:
        """Remove *callback* from the subscriber list for *session_id*."""
        try:
            _subscribers[session_id].remove(callback)
        except ValueError:
            pass

    async def publish(self, session_id: int, message: dict) -> None:
        """
        Fanout *message* to all subscribers of *session_id*.

        Delivery failures in individual callbacks are logged but do not
        interrupt delivery to other subscribers.
        """
        callbacks = list(_subscribers.get(session_id, []))
        tasks = [asyncio.create_task(cb(message)) for cb in callbacks]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for result in results:
            if isinstance(result, Exception):
                logger.warning("MessageBus delivery error: %s", result)

    def clear_session(self, session_id: int) -> None:
        """Remove all subscribers for a completed session."""
        _subscribers.pop(session_id, None)


# Singleton instance shared across the request lifecycle
message_bus = MessageBus()
