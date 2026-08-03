"""app/security/rate_limiter.py

Fixed-window in-memory rate limiter.

In production this should be replaced with a Redis-backed implementation.
The module exposes ``is_rate_limited`` (boolean check) and
``enforce_rate_limit`` (raises on breach) for use by the middleware and
dependency injection layer.
"""
from __future__ import annotations

import time
from collections import defaultdict
from typing import Dict

from app.security.constants import DEFAULT_RATE_LIMIT

# ------------------------------------------------------------------
# In-memory state
# ------------------------------------------------------------------
# { identifier -> { window_minute -> request_count } }
_buckets: Dict[str, Dict[int, int]] = defaultdict(lambda: defaultdict(int))


def _current_window() -> int:
    """Return the current 1-minute window as an integer."""
    return int(time.time()) // 60


def _get_count(identifier: str) -> int:
    window = _current_window()
    # Evict stale windows to prevent unbounded memory growth
    stale = [w for w in _buckets[identifier] if w < window]
    for w in stale:
        del _buckets[identifier][w]
    return _buckets[identifier][window]


def _increment(identifier: str) -> int:
    window = _current_window()
    _buckets[identifier][window] += 1
    return _buckets[identifier][window]


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------

def is_rate_limited(identifier: str, limit: int = DEFAULT_RATE_LIMIT) -> bool:
    """Return ``True`` if *identifier* has exceeded *limit* requests per minute.

    This check is non-mutating – it does NOT increment the counter.

    Args:
        identifier: Bucket key, e.g. ``"user:42"`` or ``"ip:1.2.3.4"``.
        limit: Maximum allowed requests per minute. Defaults to
               :data:`~app.security.constants.DEFAULT_RATE_LIMIT`.
    """
    return _get_count(identifier) >= limit


def record_request(identifier: str) -> int:
    """Increment the counter for *identifier* and return the new count."""
    return _increment(identifier)


def enforce_rate_limit(identifier: str, limit: int = DEFAULT_RATE_LIMIT) -> None:
    """Check the rate limit and raise :class:`~app.security.exceptions.RateLimitExceededError` if exceeded.

    Also records the current request.

    Args:
        identifier: Bucket key.
        limit: Maximum requests per minute.

    Raises:
        RateLimitExceededError: When the request count exceeds *limit*.
    """
    from app.security.exceptions import RateLimitExceededError

    count = record_request(identifier)
    if count > limit:
        raise RateLimitExceededError(
            f"Rate limit of {limit} requests/minute exceeded for {identifier}."
        )
