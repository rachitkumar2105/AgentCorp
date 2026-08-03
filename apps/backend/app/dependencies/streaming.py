"""
Streaming dependency injection.

Provides the ``get_streaming_service`` FastAPI dependency that constructs
and wires all layers required by ``StreamingService``.

The same collaborators are used as in ``dependencies/chat.py`` — the only
difference is that StreamingService is wired in instead of ChatService.
This guarantees zero code duplication between the chat and streaming paths.
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.agent_repository import AgentRepository
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository
from app.services.context_builder import ContextBuilder
from app.services.knowledge_service import KnowledgeService
from app.services.memory_service import MemoryService
from app.services.prompt_builder import PromptBuilder
from app.services.provider_service import ProviderService
from app.services.rag_service import RAGService
from app.services.streaming_service import StreamingService
from app.services.tool_execution_service import ToolExecutionService


def get_streaming_service(
    db: Session = Depends(get_db),
) -> StreamingService:
    """
    FastAPI dependency that builds and returns a fully wired StreamingService.

    Scoped per-request so each stream has its own DB session and no shared
    mutable state leaks between concurrent streams.

    Override this dependency in tests to inject mocks / stubs without
    modifying any service or endpoint code.
    """
    return StreamingService(
        conversation_repo=ConversationRepository(db),
        message_repo=MessageRepository(db),
        agent_repo=AgentRepository(db),
        provider_service=ProviderService(),
        context_builder=ContextBuilder(),
        prompt_builder=PromptBuilder(),
        memory_service=MemoryService(db),
        knowledge_service=KnowledgeService(db),
        rag_service=RAGService(db),
        tool_execution_service=ToolExecutionService(db),
    )
