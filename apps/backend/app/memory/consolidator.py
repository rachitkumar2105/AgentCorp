"""
Memory Engine — Consolidator.
"""

from __future__ import annotations


class Consolidator:
    """
    De-duplicates and merges overlapping memories.
    """

    def consolidate(self, memories: list[dict]) -> list[dict]:
        """Merges duplicate memories while keeping the highest confidence."""
        seen = {}
        for m in memories:
            key = m.get("title", "")
            if key not in seen:
                seen[key] = m
            else:
                if m.get("confidence_score", 0.0) > seen[key].get("confidence_score", 0.0):
                    seen[key] = m
        return list(seen.values())
