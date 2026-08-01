"""
Agent Engine — Evaluator.
"""

from __future__ import annotations


class Evaluator:
    """
    Decides final completion or escalation states.
    """

    def is_goal_achieved(
        self,
        objective: str,
        reflection_results: dict,
    ) -> bool:
        """Determines if criteria matches complete states."""
        return reflection_results.get("success", False) and reflection_results.get("confidence", 0.0) > 0.8
