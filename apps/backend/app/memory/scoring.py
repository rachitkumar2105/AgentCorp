"""
Memory Engine — Memory scoring module.
"""

from __future__ import annotations


class MemoryScorer:
    """
    Computes significance, recency and semantic weights for retrieved memory lists.
    """

    def score_memory(
        self,
        importance: float,
        confidence: float,
        recency_factor: float = 1.0,
    ) -> float:
        """Calculate weighted compound utility scores."""
        return (importance * 0.4) + (confidence * 0.3) + (recency_factor * 0.3)
