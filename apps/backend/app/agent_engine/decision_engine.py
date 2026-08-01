"""
Agent Engine — Decision Engine.
"""

from __future__ import annotations

from app.agent_engine.action_selector import ActionType


class DecisionEngine:
    """
    Selects the next discrete action based on Reasoner findings.
    """

    def select_action(
        self,
        reasoning_result: str,
        context: dict,
    ) -> ActionType:
        """Determines next action Enum mapping."""
        if reasoning_result == "RAG_REQUIRED":
            return ActionType.SEARCH_KNOWLEDGE
        if reasoning_result == "MEMORY_REQUIRED":
            return ActionType.SEARCH_MEMORY
        return ActionType.THINK
