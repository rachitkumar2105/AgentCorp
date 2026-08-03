"""
Capability dispatcher for Runtime V2 execution tasks.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from typing import Any

from app.models.user import User
from app.observability.diagnostics import register_capability_event
from app.runtime.capabilities import CapabilityRegistry, CapabilityExecutionMode, build_default_capability_registry
from app.runtime.execution import ExecutionResult, ExecutionState, ExecutionTask
from app.schemas.chat import (
    ChatCreateRequest,
    ChatContinueRequest,
    ChatRegenerateRequest,
    ChatRetryRequest,
    ChatResponseSchema,
    ConversationDetailSchema,
)
from app.schemas.streaming import StreamingChatRequest


class CapabilityDispatcher:
    """
    Routes execution tasks to the temporary Runtime V1 adapter.

    This class intentionally does not implement capability-specific logic.
    Native executors are a later phase; dispatch is the only responsibility here.
    """

    def __init__(self, runtime_v1_adapter: Any, capability_registry: CapabilityRegistry | None = None) -> None:
        self.runtime_v1_adapter = runtime_v1_adapter
        self.capability_registry = capability_registry or build_default_capability_registry(runtime_v1_adapter)

    async def dispatch_chat(
        self,
        *,
        task: ExecutionTask,
        execution_context: Any,
        payload: ChatCreateRequest | ChatContinueRequest | ChatRegenerateRequest | ChatRetryRequest,
        current_user: User,
        organization_id: int,
        conversation_id: int | None = None,
    ) -> tuple[ChatResponseSchema | ConversationDetailSchema, ExecutionResult]:
        started_at = datetime.now(timezone.utc)
        errors: tuple[str, ...] = ()
        status = ExecutionState.COMPLETED
        response: ChatResponseSchema | ConversationDetailSchema
        runtime = self.capability_registry.resolve(task.required_capability.lower())
        await register_capability_event(
            task.task_id,
            {
                "stage_name": "Capability Resolution",
                "status": "COMPLETED" if runtime else "FALLBACK",
                "capability_name": runtime.metadata.capability_name if runtime else task.required_capability,
                "task_id": task.task_id,
                "execution_state": ExecutionState.READY.value,
                "summary": f"Resolved {runtime.metadata.capability_name}." if runtime else "Resolved via fallback.",
                "warnings": (),
                "errors": (),
                "started_at": started_at.isoformat(),
                "completed_at": started_at.isoformat(),
                "duration": 0.0,
            },
        )
        response = None
        result: ExecutionResult | None = None
        if runtime and getattr(runtime.metadata, "execution_mode", None) == CapabilityExecutionMode.NATIVE:
            try:
                response, result, lifecycle = await runtime.run(
                    execution_context=execution_context,
                    task=task,
                    payload=payload,
                    current_user=current_user,
                    organization_id=organization_id,
                    conversation_id=conversation_id,
                )
                for entry in lifecycle:
                    await register_capability_event(task.task_id, entry.__dict__)
            except Exception as exc:
                status = ExecutionState.FAILED
                errors = (str(exc),)
                raise
            finally:
                completed_at = datetime.now(timezone.utc)
            final_response = response
            return final_response, result or ExecutionResult(
                task_id=task.task_id,
                status=status,
                outputs={"response_type": type(final_response).__name__},
                errors=errors,
                duration=(completed_at - started_at).total_seconds(),
                metadata={"required_capability": task.required_capability, "runtime": "CapabilityRuntimeLayer"},
                started_at=started_at.isoformat(),
                completed_at=completed_at.isoformat(),
            )

        try:
            final_response = await self.runtime_v1_adapter.execute_chat(
                execution_context=execution_context,
                payload=payload,
                current_user=current_user,
                organization_id=organization_id,
                conversation_id=conversation_id,
            )
        except Exception as exc:
            status = ExecutionState.FAILED
            errors = (str(exc),)
            raise
        finally:
            completed_at = datetime.now(timezone.utc)

        return final_response, ExecutionResult(
            task_id=task.task_id,
            status=status,
            outputs={"response_type": type(final_response).__name__},
            errors=errors,
            duration=(completed_at - started_at).total_seconds(),
            metadata={"required_capability": task.required_capability, "runtime": "RuntimeV1Adapter"},
            started_at=started_at.isoformat(),
            completed_at=completed_at.isoformat(),
        )

    async def dispatch_stream(
        self,
        *,
        task: ExecutionTask,
        execution_context: Any,
        payload: StreamingChatRequest,
        current_user: User,
        organization_id: int,
        conversation_id: int | None = None,
    ) -> AsyncGenerator[str, None]:
        runtime = self.capability_registry.resolve(task.required_capability.lower())
        if runtime and getattr(runtime.metadata, "execution_mode", None) == CapabilityExecutionMode.NATIVE and hasattr(runtime, "execute_stream"):
            async for event in runtime.execute_stream(
                execution_context=execution_context,
                task=task,
                payload=payload,
                current_user=current_user,
                organization_id=organization_id,
                conversation_id=conversation_id,
            ):
                yield event
            return
        async for event in self.runtime_v1_adapter.execute_stream(
            execution_context=execution_context,
            payload=payload,
            current_user=current_user,
            organization_id=organization_id,
            conversation_id=conversation_id,
        ):
            yield event
