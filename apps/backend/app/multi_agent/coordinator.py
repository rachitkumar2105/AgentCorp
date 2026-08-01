"""
Multi-Agent Collaboration System — Coordinator.

The Coordinator is the top-level orchestrator for a multi-agent session.
It distributes goals to participating agents, tracks progress, collects
results, and decides when the session objective is achieved.
"""

from __future__ import annotations

import logging
from typing import Any

from app.multi_agent.exceptions import CoordinatorError

logger = logging.getLogger("multi_agent.coordinator")


class Coordinator:
    """
    Manages the lifecycle of a multi-agent collaboration session.

    Responsibilities:
    - Decomposes the session goal into per-agent sub-goals.
    - Monitors agent progress via status updates.
    - Merges agent results into a unified session output.
    - Signals session completion when all sub-goals are satisfied.
    """

    def decompose_goal(
        self,
        goal: str,
        participants: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Decompose a high-level *goal* string into sub-tasks for each agent.

        Returns a list of sub-task dicts, each containing:
          - ``agent_id``: target agent
          - ``task``: sub-task description
          - ``priority``: relative priority (lower = higher priority)
        """
        if not participants:
            raise CoordinatorError("Cannot decompose goal: no participants provided.")

        sub_tasks: list[dict[str, Any]] = []
        for idx, participant in enumerate(participants):
            sub_tasks.append(
                {
                    "agent_id": participant["agent_id"],
                    "task": f"[Sub-task {idx + 1}/{len(participants)}] {goal}",
                    "priority": idx,
                }
            )

        logger.info(
            "Decomposed goal into %d sub-tasks for %d participants.",
            len(sub_tasks),
            len(participants),
        )
        return sub_tasks

    def is_session_complete(self, participant_statuses: list[str]) -> bool:
        """
        Return *True* if all participants have reported ``COMPLETED`` status.
        """
        if not participant_statuses:
            return False
        return all(s == "COMPLETED" for s in participant_statuses)

    def merge_results(
        self,
        results: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Merge individual agent results into a combined session output.

        Each *result* dict is expected to have:
          - ``agent_id``: int
          - ``output``: arbitrary payload

        Returns ``{"results": [...], "summary": str}``.
        """
        if not results:
            return {"results": [], "summary": "No results collected."}

        merged = {
            "results": results,
            "summary": (
                f"Session completed with {len(results)} agent(s) contributing results."
            ),
        }
        logger.info("Merged %d agent results into session output.", len(results))
        return merged
