"""
Capability runtime layer for Runtime V2.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Protocol

from app.runtime.execution import (
    ExecutionContext,
    ExecutionResult,
    ExecutionState,
    ExecutionTask,
)


class CapabilityExecutionMode(str, Enum):
    NATIVE = "NATIVE"
    DELEGATED = "DELEGATED"


@dataclass(frozen=True)
class CapabilityMetadata:
    capability_id: str
    capability_name: str
    version: str
    supported_task_types: tuple[str, ...]
    dependencies: tuple[str, ...]
    execution_mode: CapabilityExecutionMode
    timeout_seconds: int | None = None
    retry_count: int | None = None
    observability_metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class CapabilityLifecycleEntry:
    capability_name: str
    task_id: str
    stage_name: str
    started_at: str
    completed_at: str
    duration: float
    execution_state: ExecutionState
    status: str
    summary: str
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()


class CapabilityRuntime(Protocol):
    metadata: CapabilityMetadata

    async def initialize(self, *, execution_context: ExecutionContext, task: ExecutionTask) -> None: ...
    async def validate(self, *, execution_context: ExecutionContext, task: ExecutionTask) -> None: ...
    async def execute(self, *, execution_context: ExecutionContext, task: ExecutionTask, payload: Any, current_user: Any | None = None, organization_id: int | None = None, conversation_id: int | None = None) -> Any: ...
    async def finalize(self, *, execution_context: ExecutionContext, task: ExecutionTask, result: ExecutionResult) -> ExecutionResult: ...
    async def cleanup(self, *, execution_context: ExecutionContext, task: ExecutionTask, result: ExecutionResult) -> None: ...


class BaseCapabilityRuntime:
    def __init__(self, metadata: CapabilityMetadata, adapter: Any) -> None:
        self.metadata = metadata
        self.adapter = adapter

    async def initialize(self, *, execution_context: ExecutionContext, task: ExecutionTask) -> None:
        return None

    async def validate(self, *, execution_context: ExecutionContext, task: ExecutionTask) -> None:
        return None

    async def execute(self, *, execution_context: ExecutionContext, task: ExecutionTask, payload: Any, current_user: Any | None = None, organization_id: int | None = None, conversation_id: int | None = None) -> Any:
        return payload

    async def finalize(self, *, execution_context: ExecutionContext, task: ExecutionTask, result: ExecutionResult) -> ExecutionResult:
        return result

    async def cleanup(self, *, execution_context: ExecutionContext, task: ExecutionTask, result: ExecutionResult) -> None:
        return None

    async def run(self, *, execution_context: ExecutionContext, task: ExecutionTask, payload: Any, current_user: Any | None = None, organization_id: int | None = None, conversation_id: int | None = None) -> tuple[Any, ExecutionResult, tuple[CapabilityLifecycleEntry, ...]]:
        entries: list[CapabilityLifecycleEntry] = []
        started = datetime.now(timezone.utc)
        await self.initialize(execution_context=execution_context, task=task)
        after_init = datetime.now(timezone.utc)
        entries.append(_entry(self.metadata.capability_name, task.task_id, "Capability Initialization", started, after_init, ExecutionState.READY, "COMPLETED", "Capability runtime initialized."))
        await self.validate(execution_context=execution_context, task=task)
        after_validate = datetime.now(timezone.utc)
        entries.append(_entry(self.metadata.capability_name, task.task_id, "Capability Validation", after_init, after_validate, ExecutionState.READY, "COMPLETED", "Capability runtime validated."))
        executed = await self.execute(execution_context=execution_context, task=task, payload=payload, current_user=current_user, organization_id=organization_id, conversation_id=conversation_id)
        after_execute = datetime.now(timezone.utc)
        entries.append(_entry(self.metadata.capability_name, task.task_id, "Capability Invocation", after_validate, after_execute, ExecutionState.RUNNING, "COMPLETED", "Capability runtime invoked."))
        result = await self.finalize(
            execution_context=execution_context,
            task=task,
            result=ExecutionResult(
                task_id=task.task_id,
                status=ExecutionState.COMPLETED,
                outputs={
                    "capability_name": self.metadata.capability_name,
                    "execution_output": executed,
                },
                errors=(),
                duration=(after_execute - started).total_seconds(),
                metadata={"capability_id": self.metadata.capability_id},
                started_at=started.isoformat(),
                completed_at=after_execute.isoformat(),
            ),
        )
        after_finalize = datetime.now(timezone.utc)
        entries.append(_entry(self.metadata.capability_name, task.task_id, "Capability Completion", after_execute, after_finalize, result.status, "COMPLETED", "Capability runtime finalized."))
        await self.cleanup(execution_context=execution_context, task=task, result=result)
        after_cleanup = datetime.now(timezone.utc)
        entries.append(_entry(self.metadata.capability_name, task.task_id, "Capability Cleanup", after_finalize, after_cleanup, result.status, "COMPLETED", "Capability runtime cleaned up."))
        return executed, result, tuple(entries)


def _entry(capability_name: str, task_id: str, stage_name: str, started_at: datetime, completed_at: datetime, execution_state: ExecutionState, status: str, summary: str) -> CapabilityLifecycleEntry:
    return CapabilityLifecycleEntry(
        capability_name=capability_name,
        task_id=task_id,
        stage_name=stage_name,
        started_at=started_at.isoformat(),
        completed_at=completed_at.isoformat(),
        duration=(completed_at - started_at).total_seconds(),
        execution_state=execution_state,
        status=status,
        summary=summary,
    )


class CapabilityRegistry:
    def __init__(self) -> None:
        self._runtimes: dict[str, CapabilityRuntime] = {}

    def register(self, runtime: CapabilityRuntime) -> None:
        self._runtimes[runtime.metadata.capability_id] = runtime

    def resolve(self, capability_id: str) -> CapabilityRuntime | None:
        return self._runtimes.get(capability_id)

    def metadata(self) -> tuple[CapabilityMetadata, ...]:
        return tuple(runtime.metadata for runtime in self._runtimes.values())


class DelegatedCapabilityRuntime(BaseCapabilityRuntime):
    async def execute(self, *, execution_context: ExecutionContext, task: ExecutionTask, payload: Any, current_user: Any | None = None, organization_id: int | None = None, conversation_id: int | None = None) -> Any:
        capability_id = self.metadata.capability_id
        if capability_id == "streaming":
            async for _ in self.adapter.execute_stream(
                execution_context=execution_context,
                payload=payload,
                current_user=current_user,
                organization_id=organization_id,
                conversation_id=conversation_id,
            ):
                pass
            return {"streamed": True}
        return await self.adapter.execute_chat(
            execution_context=execution_context,
            payload=payload,
            current_user=current_user,
            organization_id=organization_id,
            conversation_id=conversation_id,
        )


def build_default_capability_registry(adapter: Any) -> CapabilityRegistry:
    registry = CapabilityRegistry()
    capabilities = (
        ("memory", "Memory Runtime Adapter", ("memory",), ("knowledge",), ("memory",)),
        ("knowledge", "Knowledge Runtime Adapter", ("knowledge",), ("rag",), ("knowledge",)),
        ("rag", "RAG Runtime Adapter", ("rag",), ("workflow",), ("rag",)),
        ("workflow", "Workflow Runtime Adapter", ("workflow",), ("tools",), ("workflow",)),
        ("tools", "Tool Runtime Adapter", ("tool", "tools"), ("provider",), ("tools",)),
        ("provider", "Provider Runtime Adapter", ("provider",), (), ("provider",)),
        ("streaming", "Streaming Runtime Adapter", ("streaming",), (), ("streaming",)),
    )
    for capability_id, capability_name, task_types, dependencies, observability in capabilities:
        registry.register(
            DelegatedCapabilityRuntime(
                CapabilityMetadata(
                    capability_id=capability_id,
                    capability_name=capability_name,
                    version="1.0",
                    supported_task_types=task_types,
                    dependencies=dependencies,
                    execution_mode=CapabilityExecutionMode.DELEGATED,
                    timeout_seconds=None,
                    retry_count=None,
                    observability_metadata={"layer": "capability_runtime", "capability": observability[0]},
                ),
                adapter,
            )
        )
    return registry
