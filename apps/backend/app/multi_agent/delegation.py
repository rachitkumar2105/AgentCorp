"""
Multi-Agent Collaboration System — Delegation Engine.

Handles task delegation from one agent (coordinator) to another (worker)
within a shared collaboration session, enforcing depth limits and recording
delegation chains.
"""

from __future__ import annotations

import logging
from typing import Any

from app.multi_agent.constants import MAX_AGENT_DELEGATIONS
from app.multi_agent.exceptions import DelegationLimitExceededError

logger = logging.getLogger("multi_agent.delegation")


class DelegationEngine:
    """
    Validates and builds delegation records for inter-agent task hand-offs.

    The engine does NOT persist anything — persistence is the responsibility
    of the service layer.  The engine only enforces policy rules and
    produces a structured delegation payload.
    """

    def validate_delegation(
        self,
        delegation_depth: int,
        from_agent_id: int,
        to_agent_id: int,
        session_participant_ids: list[int],
    ) -> None:
        """
        Raise *DelegationLimitExceededError* if delegation depth is exceeded.
        Raise *ValueError* if the target agent is not a session participant.
        """
        if delegation_depth >= MAX_AGENT_DELEGATIONS:
            raise DelegationLimitExceededError(
                f"Delegation depth {delegation_depth} exceeds maximum "
                f"{MAX_AGENT_DELEGATIONS}."
            )
        if to_agent_id not in session_participant_ids:
            raise ValueError(
                f"Agent {to_agent_id} is not a participant in this session."
            )
        if from_agent_id == to_agent_id:
            raise ValueError("An agent cannot delegate a task to itself.")

    def build_delegation_payload(
        self,
        session_id: int,
        from_agent_id: int,
        to_agent_id: int,
        task_description: str,
        context: dict[str, Any] | None,
        depth: int,
    ) -> dict[str, Any]:
        """
        Produce a structured delegation record (not yet persisted).
        """
        return {
            "session_id": session_id,
            "from_agent_id": from_agent_id,
            "to_agent_id": to_agent_id,
            "task_description": task_description,
            "context": context or {},
            "delegation_depth": depth,
            "status": "PENDING",
        }
