"""
Extended Message Repository.

Provides all message-level persistence helpers required by the Chat Engine.
Extends the minimal stub that was already in place.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.message import Message
from app.repositories.base_repository import BaseRepository


class MessageRepository(BaseRepository[Message]):
    """
    Repository for Message model operations.

    Responsibilities:
      - Persist user and assistant messages
      - Query paginated message history
      - Retrieve the last assistant message for regeneration / retry
      - Update message metadata after AI execution
    """

    def __init__(self, db: Session) -> None:
        super().__init__(Message, db)

    # ------------------------------------------------------------------
    # Existing method — unchanged
    # ------------------------------------------------------------------

    def get_by_conversation(self, conversation_id: int) -> list[Message]:
        """Retrieve all messages for a conversation ordered by id ascending."""
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.id.asc())
        )
        return list(self.db.scalars(stmt).all())

    # ------------------------------------------------------------------
    # Chat Engine helpers
    # ------------------------------------------------------------------

    def create_user_message(
        self,
        conversation_id: int,
        content: str,
    ) -> Message:
        """
        Persist a new user-role message for the given conversation.

        Returns the committed and refreshed Message instance.
        """
        message = Message(
            conversation_id=conversation_id,
            role="user",
            content=content,
        )
        return self.create(message)

    def create_assistant_message(
        self,
        conversation_id: int,
        content: str,
        *,
        provider: str | None = None,
        model_used: str | None = None,
        finish_reason: str | None = None,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        total_tokens: int | None = None,
    ) -> Message:
        """
        Persist a new assistant-role message with optional AI metadata.

        All metadata arguments are stored on the Message row so that the
        conversation history carries full provenance for audit, billing,
        and debugging.
        """
        message = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=content,
        )
        # Attach metadata only if the columns exist on the model
        _set_if_attr(message, "provider", provider)
        _set_if_attr(message, "model_used", model_used)
        _set_if_attr(message, "finish_reason", finish_reason)
        _set_if_attr(message, "prompt_tokens", prompt_tokens)
        _set_if_attr(message, "completion_tokens", completion_tokens)
        _set_if_attr(message, "total_tokens", total_tokens)

        return self.create(message)

    def get_last_assistant_message(
        self,
        conversation_id: int,
    ) -> Message | None:
        """
        Return the most recent assistant message for a conversation.

        Used by the regenerate and retry endpoints.
        """
        stmt = (
            select(Message)
            .where(
                Message.conversation_id == conversation_id,
                Message.role == "assistant",
            )
            .order_by(Message.id.desc())
            .limit(1)
        )
        return self.db.scalar(stmt)

    def get_last_user_message(
        self,
        conversation_id: int,
    ) -> Message | None:
        """
        Return the most recent user message for a conversation.

        Used by the regenerate endpoint to reconstruct the prompt.
        """
        stmt = (
            select(Message)
            .where(
                Message.conversation_id == conversation_id,
                Message.role == "user",
            )
            .order_by(Message.id.desc())
            .limit(1)
        )
        return self.db.scalar(stmt)

    def update_message_metadata(
        self,
        message: Message,
        *,
        provider: str | None = None,
        model_used: str | None = None,
        finish_reason: str | None = None,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        total_tokens: int | None = None,
    ) -> Message:
        """
        Patch metadata columns on an existing message and commit.

        Allows the Chat Service to first persist a placeholder message,
        then enrich it post-execution without another round-trip.
        """
        _set_if_attr(message, "provider", provider)
        _set_if_attr(message, "model_used", model_used)
        _set_if_attr(message, "finish_reason", finish_reason)
        _set_if_attr(message, "prompt_tokens", prompt_tokens)
        _set_if_attr(message, "completion_tokens", completion_tokens)
        _set_if_attr(message, "total_tokens", total_tokens)

        return self.update(message)

    def count_by_conversation(self, conversation_id: int) -> int:
        """Return the total number of messages in a conversation."""
        from sqlalchemy import func

        stmt = (
            select(func.count())
            .select_from(Message)
            .where(Message.conversation_id == conversation_id)
        )
        return self.db.scalar(stmt) or 0


# ---------------------------------------------------------------------------
# Internal utility
# ---------------------------------------------------------------------------


def _set_if_attr(obj: object, attr: str, value: object) -> None:
    """Set *attr* on *obj* only when the attribute is defined on the class."""
    if hasattr(obj, attr) and value is not None:
        setattr(obj, attr, value)
