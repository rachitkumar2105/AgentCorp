"""
Agent Engine — Planner.
"""

from __future__ import annotations

from app.models.goal import Goal, GoalTask


class Planner:
    """
    Decomposes goals into a set of structured subtasks.
    """

    def plan_goal(self, goal: Goal) -> list[dict]:
        """Decompose objective text into list items."""
        # Simple string parsing decomposition stub
        tasks = []
        # Fallback basic setup
        tasks.append({
            "title": f"Analyze: {goal.title}",
            "description": f"Gather details relating to {goal.objective}",
            "order": 1,
            "execution_type": "AI",
        })
        tasks.append({
            "title": "Resolve Objective",
            "description": "Execute main objectives using tools or RAG as matching queries require.",
            "order": 2,
            "execution_type": "AI",
        })
        return tasks
