"""
Workflow Engine — Transition Engine.

Determines the next node target mapping by evaluating condition statements.
"""

from __future__ import annotations

from typing import Any
from app.models.workflow import WorkflowEdge


class TransitionEngine:
    """
    Evaluates conditional edges to route transitions.
    """

    def evaluate_transition(
        self,
        edges: list[WorkflowEdge],
        context: dict[str, Any],
    ) -> int | None:
        """
        Evaluate edge expressions against context values.
        """
        # Sort edges by priority (highest priority first)
        sorted_edges = sorted(edges, key=lambda x: x.priority, reverse=True)

        for edge in sorted_edges:
            cond = edge.transition_condition
            if not cond:
                # Unconditional transition edge acts as default matching path
                return edge.target_node_id

            # Simple safe evaluator mapping equality statements
            # e.g. "status == approved" or "score > 10"
            try:
                if "==" in cond:
                    left, right = cond.split("==")
                    left_val = self._resolve_path(left.strip(), context)
                    right_val = right.strip().strip("'\"")
                    if str(left_val) == str(right_val):
                        return edge.target_node_id
            except Exception:
                continue

        return None

    def _resolve_path(self, path: str, context: dict[str, Any]) -> Any:
        # e.g., "variables.status"
        parts = path.split(".")
        val = context
        for part in parts:
            if isinstance(val, dict):
                val = val.get(part)
            else:
                return None
        return val
