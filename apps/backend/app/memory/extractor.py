"""
Memory Engine — Memory extractor.
"""

from __future__ import annotations


class MemoryExtractor:
    """
    Identifies fact candidates and preferences from dialogue histories.
    """

    def extract_memories(self, conversation_history: str) -> list[dict]:
        """
        Stub parsing logic returning mock candidates.
        """
        # Excludes smalltalk and noise, focuses on commitments/facts
        if "prefer" in conversation_history or "like" in conversation_history:
            return [{
                "title": "User preference",
                "content": "User expressed language or operational settings preference.",
                "importance_score": 0.6,
                "confidence_score": 0.8,
                "memory_type": "semantic",
            }]
        return []
