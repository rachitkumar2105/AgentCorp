"""
Multi-Agent Collaboration System — Repository Layer.

Provides data-access helpers for:
    MultiAgentSession
    MultiAgentParticipant
    AgentInterMessage
    AgentDelegation
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.multi_agent import (
    MultiAgentSession,
    MultiAgentParticipant,
    AgentInterMessage,
    AgentDelegation,
)
from app.repositories.base_repository import BaseRepository


class MultiAgentSessionRepository(BaseRepository[MultiAgentSession]):
    def __init__(self, db: Session) -> None:
        super().__init__(MultiAgentSession, db)

    # ------------------------------------------------------------------ #
    # Queries                                                              #
    # ------------------------------------------------------------------ #

    def get_by_org_and_id(
        self, organization_id: int, session_id: int
    ) -> MultiAgentSession | None:
        stmt = select(MultiAgentSession).where(
            MultiAgentSession.organization_id == organization_id,
            MultiAgentSession.id == session_id,
        )
        return self.db.scalar(stmt)

    def list_by_organization(
        self,
        organization_id: int,
        status: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[MultiAgentSession]:
        stmt = select(MultiAgentSession).where(
            MultiAgentSession.organization_id == organization_id
        )
        if status:
            stmt = stmt.where(MultiAgentSession.status == status)
        stmt = stmt.order_by(MultiAgentSession.created_at.desc()).offset(offset).limit(limit)
        return list(self.db.scalars(stmt).all())

    def list_active_by_agent(self, agent_id: int) -> list[MultiAgentSession]:
        """Return active sessions where *agent_id* is the coordinator."""
        stmt = select(MultiAgentSession).where(
            MultiAgentSession.coordinator_agent_id == agent_id,
            MultiAgentSession.status.in_(["PENDING", "RUNNING"]),
        )
        return list(self.db.scalars(stmt).all())


class MultiAgentParticipantRepository(BaseRepository[MultiAgentParticipant]):
    def __init__(self, db: Session) -> None:
        super().__init__(MultiAgentParticipant, db)

    def list_by_session(self, session_id: int) -> list[MultiAgentParticipant]:
        stmt = select(MultiAgentParticipant).where(
            MultiAgentParticipant.session_id == session_id
        )
        return list(self.db.scalars(stmt).all())

    def get_by_session_and_agent(
        self, session_id: int, agent_id: int
    ) -> MultiAgentParticipant | None:
        stmt = select(MultiAgentParticipant).where(
            MultiAgentParticipant.session_id == session_id,
            MultiAgentParticipant.agent_id == agent_id,
        )
        return self.db.scalar(stmt)

    def participant_agent_ids(self, session_id: int) -> list[int]:
        participants = self.list_by_session(session_id)
        return [p.agent_id for p in participants]


class AgentInterMessageRepository(BaseRepository[AgentInterMessage]):
    def __init__(self, db: Session) -> None:
        super().__init__(AgentInterMessage, db)

    def list_by_session(
        self,
        session_id: int,
        offset: int = 0,
        limit: int = 50,
    ) -> list[AgentInterMessage]:
        stmt = (
            select(AgentInterMessage)
            .where(AgentInterMessage.session_id == session_id)
            .order_by(AgentInterMessage.created_at.asc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def list_undelivered(self, session_id: int) -> list[AgentInterMessage]:
        stmt = select(AgentInterMessage).where(
            AgentInterMessage.session_id == session_id,
            AgentInterMessage.delivered == False,  # noqa: E712
        )
        return list(self.db.scalars(stmt).all())


class AgentDelegationRepository(BaseRepository[AgentDelegation]):
    def __init__(self, db: Session) -> None:
        super().__init__(AgentDelegation, db)

    def list_by_session(self, session_id: int) -> list[AgentDelegation]:
        stmt = select(AgentDelegation).where(
            AgentDelegation.session_id == session_id
        ).order_by(AgentDelegation.created_at.asc())
        return list(self.db.scalars(stmt).all())

    def get_depth_for_session(self, session_id: int) -> int:
        """Return the maximum delegation depth reached in this session."""
        delegations = self.list_by_session(session_id)
        if not delegations:
            return 0
        return max(d.delegation_depth for d in delegations)
