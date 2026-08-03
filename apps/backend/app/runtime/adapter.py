"""
Runtime V1 adapter for prepared execution contexts.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from app.models.user import User
from app.runtime.execution import ExecutionContext
from app.runtime.runtimes import V1Runtime
from app.schemas.chat import (
    ChatCreateRequest,
    ChatContinueRequest,
    ChatRegenerateRequest,
    ChatRetryRequest,
    ChatResponseSchema,
    ConversationDetailSchema,
)
from app.schemas.streaming import StreamingChatRequest


class RuntimeV1Adapter:
    def __init__(self, runtime: V1Runtime) -> None:
        self.runtime = runtime

    async def execute_chat(self, *, execution_context: ExecutionContext, payload: ChatCreateRequest | ChatContinueRequest | ChatRegenerateRequest | ChatRetryRequest, current_user: User, organization_id: int, conversation_id: int | None = None) -> ChatResponseSchema | ConversationDetailSchema:
        return await V1Runtime.execute_chat(
            self.runtime,
            payload=payload,
            current_user=current_user,
            organization_id=organization_id,
            conversation_id=conversation_id,
        )

    async def execute_stream(self, *, execution_context: ExecutionContext, payload: StreamingChatRequest, current_user: User, organization_id: int, conversation_id: int | None = None) -> AsyncGenerator[str, None]:
        async for event in V1Runtime.execute_stream(
            self.runtime,
            payload=payload,
            current_user=current_user,
            organization_id=organization_id,
            conversation_id=conversation_id,
        ):
            yield event
