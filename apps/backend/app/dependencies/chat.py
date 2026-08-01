"""
Chat dependency injection.

Provides the ``get_chat_service`` FastAPI dependency that constructs and
wires all layers required by ``ChatService``.  This is the only place
where ChatService is ever instantiated — keeping the rest of the codebase
free of manual construction.

Wiring order:
  DB session
    └─ ConversationRepository
    └─ MessageRepository
    └─ AgentRepository
  ProviderService (stateless, constructed per-request)
  ContextBuilder  (stateless singleton-like)
  PromptBuilder   (stateless singleton-like)
    ↓
  ChatService
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.agent_repository import AgentRepository
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository
from app.services.chat_service import ChatService
from app.services.context_builder import ContextBuilder
from app.services.prompt_builder import PromptBuilder
from app.services.provider_service import ProviderService


def get_chat_service(
    db: Session = Depends(get_db),
) -> ChatService:
    """
    FastAPI dependency that builds and returns a fully wired ChatService.

    All inner collaborators are constructed here so that:
      - No manual instantiation is needed in endpoint handlers.
      - Swapping any collaborator (e.g. for testing) requires only
        overriding this single dependency.
      - Each request gets its own ChatService bound to its own DB session.
    """
    conversation_repo = ConversationRepository(db)
    message_repo = MessageRepository(db)
    agent_repo = AgentRepository(db)
    provider_service = ProviderService()
    context_builder = ContextBuilder()
    prompt_builder = PromptBuilder()

    return ChatService(
        conversation_repo=conversation_repo,
        message_repo=message_repo,
        agent_repo=agent_repo,
        provider_service=provider_service,
        context_builder=context_builder,
        prompt_builder=prompt_builder,
    )
