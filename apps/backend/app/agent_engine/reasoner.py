"""
Agent Engine — Reasoner.
"""

from __future__ import annotations


class Reasoner:
    """
    Evaluates context state information to determine operational missing gaps.
    """

    def reason_state(
        self,
        objective: str,
        context: dict,
    ) -> str:
        """Determines missing parts of knowledge, tools or memory mappings."""
        # Simple rule matcher stub
        if "policy" in objective or "handbook" in objective:
            return "RAG_REQUIRED"
        if "user" in objective or "preferences" in objective:
            return "MEMORY_REQUIRED"
        return "DEFAULT"
