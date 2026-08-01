"""
Extended Conversation Repository.

Adds pagination-aware queries and eager-loaded conversation+messages
retrieval needed by the Chat Engine.  All original behaviour is preserved.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.conversation import Conversation
from app.models.message import Message
from app.repositories.base_repository import BaseRepository


class ConversationRepository(BaseRepository[Conversation]):
    """
    Repository for Conversation model operations.

    Extends the base CRUD with chat-engine-specific query helpers that
    avoid duplicate DB round-trips through selective eager loading.
    """

    def __init__(self, db: Session) -> None:
        super().__init__(Conversation, db)

    # ------------------------------------------------------------------
    # Existing method — unchanged
    # ------------------------------------------------------------------

    def get_by_org(self, organization_id: int) -> list[Conversation]:
        """Retrieve all conversations for an organisation."""
        stmt = select(Conversation).where(
            Conversation.organization_id == organization_id
        )
        return list(self.db.scalars(stmt).all())

    # ------------------------------------------------------------------
    # Chat Engine helpers
    # ------------------------------------------------------------------

    def get_by_id_for_org(
        self,
        conversation_id: int,
        organization_id: int,
    ) -> Conversation | None:
        """
        Retrieve a single conversation that belongs to the given organisation.

        Returns None if the conversation does not exist or belongs to a
        different organisation (prevents cross-tenant data leakage).
        """
        stmt = (
            select(Conversation)
            .where(
                Conversation.id == conversation_id,
                Conversation.organization_id == organization_id,
            )
        )
        return self.db.scalar(stmt)

    def get_with_messages(
        self,
        conversation_id: int,
        organization_id: int,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[Conversation | None, list[Message], int]:
        """
        Fetch a conversation together with a paginated slice of its messages.

        Returns a 3-tuple of:
          - Conversation (or None if not found / wrong org)
          - Paginated list of Message rows ordered by id ascending
          - Total message count for that conversation

        A single round-trip is used for the conversation; messages are fetched
        in a separate query so pagination is applied cleanly.
        """
        conv_stmt = (
            select(Conversation)
            .where(
                Conversation.id == conversation_id,
                Conversation.organization_id == organization_id,
            )
        )
        conversation = self.db.scalar(conv_stmt)

        if conversation is None:
            return None, [], 0

        # Count total messages
        count_stmt = (
            select(func.count())
            .select_from(Message)
            .where(Message.conversation_id == conversation_id)
        )
        total: int = self.db.scalar(count_stmt) or 0

        # Fetch paginated messages
        msg_stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.id.asc())
            .offset(offset)
            .limit(limit)
        )
        messages = list(self.db.scalars(msg_stmt).all())

        return conversation, messages, total

    def get_by_user_and_org(
        self,
        user_id: int,
        organization_id: int,
    ) -> list[Conversation]:
        """
        List all conversations for a specific user within an organisation.
        Ordered newest first.
        """
        stmt = (
            select(Conversation)
            .where(
                Conversation.user_id == user_id,
                Conversation.organization_id == organization_id,
            )
            .order_by(Conversation.created_at.desc())
        )
        return list(self.db.scalars(stmt).all())
