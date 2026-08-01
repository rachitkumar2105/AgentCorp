"""
Memory Engine — Forgetting.
"""

from __future__ import annotations

from datetime import datetime, timezone


class ForgettingStrategy:
    """
    Implements expiration, low-priority pruning, and archiving.
    """

    def should_prune(self, importance_score: float, confidence_score: float) -> bool:
        """Determines if a memory should be forgotten based on low importance."""
        return importance_score < 0.2 and confidence_score < 0.3

    def is_expired(self, expires_at: datetime | None) -> bool:
        """Check if expiration date has passed."""
        if expires_at is None:
            return False
        return expires_at < datetime.now(timezone.utc)
