"""
Runtime router dependency wiring.
"""

from __future__ import annotations

from fastapi import Depends

from app.db.session import get_db
from app.dependencies.chat import get_chat_service
from app.dependencies.streaming import get_streaming_service
from app.runtime.router import RuntimeRouter
from app.runtime.runtimes import V1Runtime, V2Runtime
from app.runtime.cognitive import CognitiveEngine
from app.services.context_builder import ContextBuilder
from app.services.chat_service import ChatService
from app.services.knowledge_service import KnowledgeService
from app.services.memory_service import MemoryService
from app.services.provider_service import ProviderService
from app.services.rag_service import RAGService
from app.services.streaming_service import StreamingService
from app.services.tool_execution_service import ToolExecutionService
from app.services.workflow_service import WorkflowService
from app.repositories.agent_repository import AgentRepository
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository
from app.services.prompt_builder import PromptBuilder


def get_runtime_router(
    db = Depends(get_db),
) -> RuntimeRouter:
    conversation_repo = ConversationRepository(db)
    message_repo = MessageRepository(db)
    agent_repo = AgentRepository(db)
    provider_service = ProviderService()
    context_builder = ContextBuilder()
    prompt_builder = PromptBuilder()
    memory_service = MemoryService(db)
    knowledge_service = KnowledgeService(db)
    rag_service = RAGService(db)
    tool_execution_service = ToolExecutionService(db)
    workflow_service = WorkflowService(db)
    chat_service = ChatService(
        conversation_repo=conversation_repo,
        message_repo=message_repo,
        agent_repo=agent_repo,
        provider_service=provider_service,
        context_builder=context_builder,
        prompt_builder=prompt_builder,
        memory_service=memory_service,
        knowledge_service=knowledge_service,
        rag_service=rag_service,
        tool_execution_service=tool_execution_service,
    )
    streaming_service = StreamingService(
        conversation_repo=conversation_repo,
        message_repo=message_repo,
        agent_repo=agent_repo,
        provider_service=provider_service,
        context_builder=context_builder,
        prompt_builder=prompt_builder,
        memory_service=memory_service,
        knowledge_service=knowledge_service,
        rag_service=rag_service,
        tool_execution_service=tool_execution_service,
    )
    v1_runtime = V1Runtime(chat_service=chat_service, streaming_service=streaming_service)
    v2_runtime = V2Runtime(
        chat_service=chat_service,
        streaming_service=streaming_service,
        cognitive_engine=CognitiveEngine(),
        memory_service=memory_service,
        knowledge_service=knowledge_service,
        rag_service=rag_service,
        workflow_service=workflow_service,
        tool_execution_service=tool_execution_service,
        provider_service=provider_service,
    )
    return RuntimeRouter(v1_runtime=v1_runtime, v2_runtime=v2_runtime)
