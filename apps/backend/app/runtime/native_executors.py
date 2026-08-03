"""
Native capability executors for Runtime V2.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator, Awaitable, Callable
from typing import Any

from app.models.user import User
from app.providers.schemas import ChatRequest
from app.runtime.capabilities import BaseCapabilityRuntime, CapabilityExecutionMode, CapabilityMetadata, CapabilityRegistry
from app.runtime.execution import ExecutionContext, ExecutionResult, ExecutionState, ExecutionTask
from app.schemas.tool_execution import ToolCallRequest, ToolExecutionResult


ExecutorFn = Callable[[ExecutionContext, ExecutionTask, Any, User | None, int | None, int | None], Awaitable[tuple[Any, dict[str, Any]]]]


class ServiceBackedCapabilityRuntime(BaseCapabilityRuntime):
    def __init__(self, metadata: CapabilityMetadata, adapter: Any, service_name: str, executor: ExecutorFn) -> None:
        super().__init__(metadata, adapter)
        self.service_name = service_name
        self._executor = executor

    async def execute(
        self,
        *,
        execution_context: ExecutionContext,
        task: ExecutionTask,
        payload: Any,
        current_user: User | None = None,
        organization_id: int | None = None,
        conversation_id: int | None = None,
    ) -> Any:
        output, _ = await self._executor(execution_context, task, payload, current_user, organization_id, conversation_id)
        return output

    async def finalize(self, *, execution_context: ExecutionContext, task: ExecutionTask, result: ExecutionResult) -> ExecutionResult:
        metadata = dict(result.metadata)
        metadata["service_name"] = self.service_name
        return ExecutionResult(
            task_id=result.task_id,
            status=result.status,
            outputs=result.outputs,
            errors=result.errors,
            duration=result.duration,
            metadata=metadata,
            started_at=result.started_at,
            completed_at=result.completed_at,
        )

    async def run(
        self,
        *,
        execution_context: ExecutionContext,
        task: ExecutionTask,
        payload: Any,
        current_user: User | None = None,
        organization_id: int | None = None,
        conversation_id: int | None = None,
    ) -> tuple[Any, ExecutionResult, tuple[Any, ...]]:
        output, payload_metadata = await self._executor(execution_context, task, payload, current_user, organization_id, conversation_id)
        result = ExecutionResult(
            task_id=task.task_id,
            status=ExecutionState.COMPLETED,
            outputs={
                "capability_name": self.metadata.capability_name,
                "execution_output": output,
                "service_name": self.service_name,
            },
            errors=(),
            duration=float(payload_metadata.get("duration", 0.0)),
            metadata={
                "capability_id": self.metadata.capability_id,
                "service_name": self.service_name,
                **payload_metadata,
            },
            started_at=payload_metadata["started_at"],
            completed_at=payload_metadata["completed_at"],
        )
        return output, result, ()

    async def execute_stream(
        self,
        *,
        execution_context: ExecutionContext,
        task: ExecutionTask,
        payload: Any,
        current_user: User | None = None,
        organization_id: int | None = None,
        conversation_id: int | None = None,
    ) -> AsyncGenerator[Any, None]:
        if self.metadata.capability_id != "streaming":
            raise NotImplementedError
        async for chunk in self._executor_stream(execution_context, task, payload, current_user, organization_id, conversation_id):
            yield chunk

    async def _executor_stream(
        self,
        execution_context: ExecutionContext,
        task: ExecutionTask,
        payload: Any,
        current_user: User | None,
        organization_id: int | None,
        conversation_id: int | None,
    ) -> AsyncGenerator[Any, None]:
        async for chunk in self.adapter.execute_stream(
            execution_context=execution_context,
            payload=payload,
            current_user=current_user,
            organization_id=organization_id or 0,
            conversation_id=conversation_id,
        ):
            yield chunk


def _default_payload_message(payload: Any) -> str:
    return getattr(payload, "message", "") or str(payload)


def build_native_capability_registry(
    *,
    adapter: Any,
    memory_service: Any,
    knowledge_service: Any,
    rag_service: Any,
    workflow_service: Any,
    tool_execution_service: Any,
    provider_service: Any,
    streaming_service: Any,
) -> CapabilityRegistry:
    from datetime import datetime, timezone

    def wrap(service_name: str, capability_id: str, capability_name: str, executor: ExecutorFn, supported_task_types: tuple[str, ...]) -> ServiceBackedCapabilityRuntime:
        return ServiceBackedCapabilityRuntime(
            CapabilityMetadata(
                capability_id=capability_id,
                capability_name=capability_name,
                version="1.0",
                supported_task_types=supported_task_types,
                dependencies=(),
                execution_mode=CapabilityExecutionMode.NATIVE,
                observability_metadata={"layer": "native_executor", "service": service_name},
            ),
            adapter,
            service_name,
            executor,
        )

    async def memory_exec(ctx: ExecutionContext, task: ExecutionTask, payload: Any, current_user: User | None, organization_id: int | None, conversation_id: int | None) -> tuple[Any, dict[str, Any]]:
        started = datetime.now(timezone.utc)
        query = task.execution_metadata.get("query") if task.execution_metadata else None
        query = query or _default_payload_message(payload)
        agent_id = task.execution_metadata.get("agent_id") if task.execution_metadata else None
        org_id = organization_id or task.execution_metadata.get("organization_id")
        memories = await memory_service.retrieve_memories(org_id, agent_id or 0, query, top_k=task.execution_metadata.get("top_k", 5) if task.execution_metadata else 5)
        completed = datetime.now(timezone.utc)
        return [getattr(memory, "id", None) for memory in memories], {"started_at": started.isoformat(), "completed_at": completed.isoformat(), "duration": (completed - started).total_seconds()}

    async def knowledge_exec(ctx: ExecutionContext, task: ExecutionTask, payload: Any, current_user: User | None, organization_id: int | None, conversation_id: int | None) -> tuple[Any, dict[str, Any]]:
        started = datetime.now(timezone.utc)
        org_id = organization_id or task.execution_metadata.get("organization_id") if task.execution_metadata else organization_id
        kb_id = task.execution_metadata.get("kb_id") if task.execution_metadata else None
        if kb_id is None:
            output = [kb.name for kb in knowledge_service.list_knowledge_bases(org_id)]
        else:
            output = [doc.filename for doc in knowledge_service.list_documents(kb_id)]
        completed = datetime.now(timezone.utc)
        return output, {"started_at": started.isoformat(), "completed_at": completed.isoformat(), "duration": (completed - started).total_seconds()}

    async def rag_exec(ctx: ExecutionContext, task: ExecutionTask, payload: Any, current_user: User | None, organization_id: int | None, conversation_id: int | None) -> tuple[Any, dict[str, Any]]:
        started = datetime.now(timezone.utc)
        kb_id = task.execution_metadata.get("kb_id") if task.execution_metadata else None
        query = task.execution_metadata.get("query") if task.execution_metadata else None
        context = await rag_service.retrieve_context(kb_id=kb_id or 0, query=query or _default_payload_message(payload), top_k=task.execution_metadata.get("top_k", 5) if task.execution_metadata else 5, max_tokens=task.execution_metadata.get("max_tokens", 2000) if task.execution_metadata else 2000)
        completed = datetime.now(timezone.utc)
        return context, {"started_at": started.isoformat(), "completed_at": completed.isoformat(), "duration": (completed - started).total_seconds()}

    async def workflow_exec(ctx: ExecutionContext, task: ExecutionTask, payload: Any, current_user: User | None, organization_id: int | None, conversation_id: int | None) -> tuple[Any, dict[str, Any]]:
        started = datetime.now(timezone.utc)
        workflow_id = task.execution_metadata.get("workflow_id") if task.execution_metadata else None
        agent_id = task.execution_metadata.get("agent_id") if task.execution_metadata else 0
        if workflow_id is None or current_user is None:
            output = {"skipped": True, "reason": "workflow_id missing"}
        else:
            execution = await workflow_service.execute_workflow(workflow_id=workflow_id, organization_id=organization_id or 0, agent_id=agent_id, current_user=current_user)
            output = {"execution_id": execution.id, "status": execution.status}
        completed = datetime.now(timezone.utc)
        return output, {"started_at": started.isoformat(), "completed_at": completed.isoformat(), "duration": (completed - started).total_seconds()}

    async def tools_exec(ctx: ExecutionContext, task: ExecutionTask, payload: Any, current_user: User | None, organization_id: int | None, conversation_id: int | None) -> tuple[Any, dict[str, Any]]:
        started = datetime.now(timezone.utc)
        calls = task.execution_metadata.get("tool_calls") if task.execution_metadata else None
        if not calls:
            output = {"skipped": True, "reason": "tool_calls missing"}
        else:
            result: ToolExecutionResult = await tool_execution_service.execute_batch(
                requests=[ToolCallRequest(**call) for call in calls],
                current_user=current_user,
                organization_id=organization_id or 0,
                agent_id=task.execution_metadata.get("agent_id", 0) if task.execution_metadata else 0,
                conversation_id=conversation_id or 0,
            )
            output = result.model_dump()
        completed = datetime.now(timezone.utc)
        return output, {"started_at": started.isoformat(), "completed_at": completed.isoformat(), "duration": (completed - started).total_seconds()}

    async def provider_exec(ctx: ExecutionContext, task: ExecutionTask, payload: Any, current_user: User | None, organization_id: int | None, conversation_id: int | None) -> tuple[Any, dict[str, Any]]:
        started = datetime.now(timezone.utc)
        if isinstance(payload, ChatRequest):
            response = await provider_service.chat(payload, provider_name=getattr(payload, "provider", None), mode="AUTO")
            output = response.model_dump()
        else:
            output = await provider_service.list_models(getattr(payload, "provider", None))
        completed = datetime.now(timezone.utc)
        return output, {"started_at": started.isoformat(), "completed_at": completed.isoformat(), "duration": (completed - started).total_seconds()}

    async def streaming_exec(ctx: ExecutionContext, task: ExecutionTask, payload: Any, current_user: User | None, organization_id: int | None, conversation_id: int | None) -> tuple[Any, dict[str, Any]]:
        started = datetime.now(timezone.utc)
        consumed = 0
        async for _chunk in streaming_service.stream_new_chat(payload=payload, current_user=current_user, organization_id=organization_id or 0):
            consumed += 1
        completed = datetime.now(timezone.utc)
        return {"streamed_chunks": consumed}, {"started_at": started.isoformat(), "completed_at": completed.isoformat(), "duration": (completed - started).total_seconds()}

    registry = CapabilityRegistry()
    for runtime in (
        wrap("MemoryService", "memory", "Memory Runtime Adapter", memory_exec, ("memory",)),
        wrap("KnowledgeService", "knowledge", "Knowledge Runtime Adapter", knowledge_exec, ("knowledge",)),
        wrap("RAGService", "rag", "RAG Runtime Adapter", rag_exec, ("rag",)),
        wrap("WorkflowService", "workflow", "Workflow Runtime Adapter", workflow_exec, ("workflow",)),
        wrap("ToolExecutionService", "tools", "Tool Runtime Adapter", tools_exec, ("tool", "tools")),
        wrap("ProviderService", "provider", "Provider Runtime Adapter", provider_exec, ("provider",)),
        wrap("StreamingService", "streaming", "Streaming Runtime Adapter", streaming_exec, ("streaming",)),
    ):
        registry.register(runtime)
    return registry
