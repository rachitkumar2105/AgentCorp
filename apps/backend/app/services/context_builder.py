"""
Context Builder to organize conversation history into provider-agnostic schemas.
"""

import logging

from app.models.message import Message
from app.providers.schemas import ChatMessage, MessageRole

logger = logging.getLogger(__name__)


class ContextBuilder:
    """
    Builds context window for AI execution.
    Handles message history sorting, validation, and token limit formatting.
    """

    def build_context(self, db_messages: list[Message]) -> list[ChatMessage]:
        """
        Convert database messages to generic provider ChatMessage models.
        Preserves original database ordering.
        """
        chat_messages: list[ChatMessage] = []

        for msg in db_messages:
            # Ensure safe mapping of message roles
            try:
                role_val = msg.role.lower()
                role = MessageRole(role_val)
            except ValueError:
                logger.warning(f"Unknown message role: {msg.role}. Defaulting to USER.")
                role = MessageRole.USER

            chat_messages.append(ChatMessage(
                role=role,
                content=msg.content
            ))

        logger.debug(f"ContextBuilder: Compiled {len(chat_messages)} context messages.")
        return chat_messages
