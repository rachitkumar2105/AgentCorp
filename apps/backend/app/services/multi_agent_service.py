"""
Multi-Agent Collaboration System — Service Layer.

Orchestrates multi-agent sessions by delegating to:
    - AgentEngineService   (per-agent execution)
    - WorkflowService      (workflow-based sub-tasks)
    - MemoryService        (shared memory)
    - RAGService           (knowledge retrieval)
    - ToolService          (tool access)
    - MessageBus           (real-time inter-agent messaging)
    - Coordinator          (goal decomposition & result merging)
    - DelegationEngine     (depth-safe task delegation)
    - SharedContextManager (in-memory context cache)
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.multi_agent.coordinator import Coordinator
from app.multi_agent.delegation import DelegationEngine
from app.multi_agent.context_manager import SharedContextManager
from app.multi_agent.message_bus import message_bus
from app.multi_agent.exceptions import (
    SessionNotFoundError,
    AgentNotParticipantError,
    DelegationNotFoundError,
)
from app.models.multi_agent import (
    MultiAgentSession,
    MultiAgentParticipant,
    AgentInterMessage,
    AgentDelegation,
)
from app.repositories.multi_agent_repository import (
    MultiAgentSessionRepository,
    MultiAgentParticipantRepository,
    AgentInterMessageRepository,
    AgentDelegationRepository,
)
from app.services.agent_engine_service import AgentEngineService
from app.models.user import User

logger = logging.getLogger("multi_agent_service")


class MultiAgentService:
    """
    High-level service coordinating multi-agent collaboration sessions.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.session_repo = MultiAgentSessionRepository(db)
        self.participant_repo = MultiAgentParticipantRepository(db)
        self.message_repo = AgentInterMessageRepository(db)
        self.delegation_repo = AgentDelegationRepository(db)
        self.coordinator = Coordinator()
        self.delegation_engine = DelegationEngine()
        self.agent_engine = AgentEngineService(db)

    # ------------------------------------------------------------------ #
    # Session lifecycle                                                    #
    # ------------------------------------------------------------------ #

    def create_session(
        self,
        organization_id: int,
        coordinator_agent_id: int,
        name: str,
        goal: str,
        participant_agent_ids: list[int],
        shared_context: dict[str, Any] | None,
        current_user: User,
    ) -> MultiAgentSession:
        """
        Create a new collaboration session, enrol participants, and decompose
        the goal into per-agent sub-tasks.
        """
        session = MultiAgentSession(
            organization_id=organization_id,
            coordinator_agent_id=coordinator_agent_id,
            name=name,
            goal=goal,
            status="PENDING",
            shared_context=shared_context or {},
            created_by=current_user.id,
        )
        session = self.session_repo.create(session)
        logger.info(
            "Created multi-agent session %d for org %d", session.id, organization_id
        )

        # Enrol coordinator as a participant with the "coordinator" role
        all_agent_ids = [coordinator_agent_id] + [
            a for a in participant_agent_ids if a != coordinator_agent_id
        ]
        participants_meta = [{"agent_id": aid} for aid in all_agent_ids]

        # Decompose goal into sub-tasks
        sub_tasks = self.coordinator.decompose_goal(goal, participants_meta)

        for st in sub_tasks:
            role = "coordinator" if st["agent_id"] == coordinator_agent_id else "worker"
            participant = MultiAgentParticipant(
                session_id=session.id,
                agent_id=st["agent_id"],
                role=role,
                sub_task=st["task"],
                status="PENDING",
            )
            self.participant_repo.create(participant)

        return session

    def get_session(
        self, organization_id: int, session_id: int
    ) -> MultiAgentSession:
        session = self.session_repo.get_by_org_and_id(organization_id, session_id)
        if not session:
            raise SessionNotFoundError(f"Session {session_id} not found.")
        return session

    def list_sessions(
        self,
        organization_id: int,
        status: str | None,
        offset: int,
        limit: int,
    ) -> list[MultiAgentSession]:
        return self.session_repo.list_by_organization(
            organization_id, status=status, offset=offset, limit=limit
        )

    async def start_session(
        self, organization_id: int, session_id: int
    ) -> MultiAgentSession:
        """Transition session to RUNNING and fan-out sub-tasks to agents."""
        session = self.get_session(organization_id, session_id)
        if session.status not in ("PENDING",):
            raise ValueError(
                f"Session is in state '{session.status}' and cannot be started."
            )

        session.status = "RUNNING"
        session.started_at = datetime.now(timezone.utc)
        self.session_repo.update(session)

        # Publish start event to all subscribers
        await message_bus.publish(
            session_id,
            {
                "event": "session_started",
                "session_id": session_id,
                "goal": session.goal,
            },
        )
        logger.info("Started multi-agent session %d", session_id)
        return session

    async def complete_session(
        self, organization_id: int, session_id: int
    ) -> MultiAgentSession:
        """Collect results, merge them, and mark the session as COMPLETED."""
        start = time.perf_counter()
        session = self.get_session(organization_id, session_id)

        participants = self.participant_repo.list_by_session(session_id)
        results = [
            {"agent_id": p.agent_id, "output": p.result}
            for p in participants
            if p.result is not None
        ]
        merged = self.coordinator.merge_results(results)

        session.status = "COMPLETED"
        session.completed_at = datetime.now(timezone.utc)
        session.duration = time.perf_counter() - start
        session.result = merged
        self.session_repo.update(session)

        await message_bus.publish(
            session_id,
            {"event": "session_completed", "session_id": session_id, "result": merged},
        )
        message_bus.clear_session(session_id)
        logger.info("Completed multi-agent session %d", session_id)
        return session

    def cancel_session(
        self, organization_id: int, session_id: int
    ) -> MultiAgentSession:
        session = self.get_session(organization_id, session_id)
        session.status = "CANCELLED"
        session.completed_at = datetime.now(timezone.utc)
        self.session_repo.update(session)
        message_bus.clear_session(session_id)
        logger.info("Cancelled multi-agent session %d", session_id)
        return session

    # ------------------------------------------------------------------ #
    # Shared context                                                       #
    # ------------------------------------------------------------------ #

    def update_shared_context(
        self,
        organization_id: int,
        session_id: int,
        updates: dict[str, Any],
    ) -> MultiAgentSession:
        session = self.get_session(organization_id, session_id)
        ctx = SharedContextManager(session.shared_context)
        ctx.merge(updates)
        session.shared_context = ctx.snapshot()
        self.session_repo.update(session)
        return session

    # ------------------------------------------------------------------ #
    # Delegation                                                           #
    # ------------------------------------------------------------------ #

    def delegate_task(
        self,
        organization_id: int,
        session_id: int,
        from_agent_id: int,
        to_agent_id: int,
        task_description: str,
        context: dict[str, Any] | None,
    ) -> AgentDelegation:
        session = self.get_session(organization_id, session_id)
        participant_ids = self.participant_repo.participant_agent_ids(session_id)
        current_depth = self.delegation_repo.get_depth_for_session(session_id)

        self.delegation_engine.validate_delegation(
            delegation_depth=current_depth,
            from_agent_id=from_agent_id,
            to_agent_id=to_agent_id,
            session_participant_ids=participant_ids,
        )

        payload = self.delegation_engine.build_delegation_payload(
            session_id=session_id,
            from_agent_id=from_agent_id,
            to_agent_id=to_agent_id,
            task_description=task_description,
            context=context,
            depth=current_depth + 1,
        )

        delegation = AgentDelegation(**payload)
        return self.delegation_repo.create(delegation)

    def resolve_delegation(
        self,
        organization_id: int,
        session_id: int,
        delegation_id: int,
        status: str,
        result: dict[str, Any] | None,
    ) -> AgentDelegation:
        _ = self.get_session(organization_id, session_id)
        delegation = self.delegation_repo.get(delegation_id)
        if not delegation or delegation.session_id != session_id:
            raise DelegationNotFoundError(f"Delegation {delegation_id} not found.")
        delegation.status = status
        delegation.result = result
        delegation.resolved_at = datetime.now(timezone.utc)
        return self.delegation_repo.update(delegation)

    def list_delegations(
        self, organization_id: int, session_id: int
    ) -> list[AgentDelegation]:
        _ = self.get_session(organization_id, session_id)
        return self.delegation_repo.list_by_session(session_id)

    # ------------------------------------------------------------------ #
    # Messaging                                                            #
    # ------------------------------------------------------------------ #

    async def send_message(
        self,
        organization_id: int,
        session_id: int,
        from_agent_id: int,
        to_agent_id: int | None,
        message_type: str,
        content: dict[str, Any],
    ) -> AgentInterMessage:
        session = self.get_session(organization_id, session_id)
        participant_ids = self.participant_repo.participant_agent_ids(session_id)
        if from_agent_id not in participant_ids:
            raise AgentNotParticipantError(
                f"Agent {from_agent_id} is not a participant in session {session_id}."
            )

        msg = AgentInterMessage(
            session_id=session_id,
            from_agent_id=from_agent_id,
            to_agent_id=to_agent_id,
            message_type=message_type,
            content=content,
            delivered=False,
        )
        msg = self.message_repo.create(msg)

        # Fan-out via message bus
        event = {
            "event": "agent_message",
            "message_id": msg.id,
            "from_agent_id": from_agent_id,
            "to_agent_id": to_agent_id,
            "message_type": message_type,
            "content": content,
        }
        await message_bus.publish(session_id, event)

        msg.delivered = True
        self.message_repo.update(msg)
        return msg

    def list_messages(
        self,
        organization_id: int,
        session_id: int,
        offset: int,
        limit: int,
    ) -> list[AgentInterMessage]:
        _ = self.get_session(organization_id, session_id)
        return self.message_repo.list_by_session(session_id, offset=offset, limit=limit)

    # ------------------------------------------------------------------ #
    # Participant management                                               #
    # ------------------------------------------------------------------ #

    def update_participant_status(
        self,
        organization_id: int,
        session_id: int,
        agent_id: int,
        status: str,
        result: dict[str, Any] | None,
    ) -> MultiAgentParticipant:
        _ = self.get_session(organization_id, session_id)
        participant = self.participant_repo.get_by_session_and_agent(session_id, agent_id)
        if not participant:
            raise AgentNotParticipantError(
                f"Agent {agent_id} is not a participant in session {session_id}."
            )
        participant.status = status
        if result is not None:
            participant.result = result
        if status in ("COMPLETED", "FAILED"):
            participant.completed_at = datetime.now(timezone.utc)
        return self.participant_repo.update(participant)
