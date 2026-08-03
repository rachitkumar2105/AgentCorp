"""
Execution context and lifecycle tracing for Runtime V2.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import Enum
from typing import Any
import uuid

from app.runtime.cognitive import CognitiveState
from app.runtime.planning import ExecutionBlueprint


@dataclass(frozen=True)
class ExecutionMetadata:
    runtime_version: str
    request_id: str
    trace_id: str
    execution_id: str
    created_at: str


@dataclass(frozen=True)
class RuntimeLifecycleEntry:
    stage_name: str
    started_at: str
    completed_at: str
    duration: float
    status: str
    summary: str
    confidence: float | None = None
    request_id: str | None = None
    trace_id: str | None = None
    runtime_version: str | None = None
    input_snapshot: dict[str, Any] | None = None
    output_snapshot: dict[str, Any] | None = None
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()


class ExecutionState(str, Enum):
    INITIALIZED = "INITIALIZED"
    READY = "READY"
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True)
class ExecutionStateTransition:
    from_state: ExecutionState | None
    to_state: ExecutionState
    timestamp: str
    task_id: str | None = None
    summary: str = ""


@dataclass(frozen=True)
class ExecutionTask:
    task_id: str
    title: str
    description: str
    required_capability: str
    current_state: ExecutionState
    dependencies: tuple[str, ...] = ()
    priority: int = 0
    execution_metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class ExecutionResult:
    task_id: str
    status: ExecutionState
    outputs: dict[str, Any]
    errors: tuple[str, ...]
    duration: float
    metadata: dict[str, Any]
    started_at: str
    completed_at: str


@dataclass(frozen=True)
class ExecutionRun:
    execution_id: str
    state: ExecutionState
    tasks: tuple[ExecutionTask, ...]
    results: tuple[ExecutionResult, ...]
    transitions: tuple[ExecutionStateTransition, ...]
    timeline: tuple[RuntimeLifecycleEntry, ...]


@dataclass(frozen=True)
class ExecutionContext:
    original_request: Any
    runtime_version: str
    cognitive_state: CognitiveState | None = None
    execution_blueprint: ExecutionBlueprint | None = None
    execution_metadata: ExecutionMetadata | None = None
    runtime_capabilities: tuple[str, ...] = ()
    observability_references: tuple[str, ...] = ()
    trace_ids: tuple[str, ...] = ()
    execution_timestamps: tuple[str, ...] = ()
    cancellation_token: Any | None = None
    execution_state: str | None = None
    shared_runtime_metadata: dict[str, Any] | None = None
    execution_trace: tuple[RuntimeLifecycleEntry, ...] = ()

    def with_updates(self, **kwargs: Any) -> "ExecutionContext":
        return replace(self, **kwargs)


def create_execution_context(
    *,
    original_request: Any,
    runtime_version: str,
    request_id: str | None = None,
    trace_id: str | None = None,
) -> ExecutionContext:
    now = datetime.now(timezone.utc).isoformat()
    request_id = request_id or str(uuid.uuid4())
    trace_id = trace_id or str(uuid.uuid4())
    metadata = ExecutionMetadata(
        runtime_version=runtime_version,
        request_id=request_id,
        trace_id=trace_id,
        execution_id=str(uuid.uuid4()),
        created_at=now,
    )
    return ExecutionContext(
        original_request=original_request,
        runtime_version=runtime_version,
        execution_metadata=metadata,
        shared_runtime_metadata={
            "request_id": request_id,
            "trace_id": trace_id,
            "execution_id": metadata.execution_id,
        },
        runtime_capabilities=(),
        observability_references=(),
        trace_ids=(trace_id,),
        execution_timestamps=(now,),
        cancellation_token=None,
        execution_state=ExecutionState.INITIALIZED.value,
    )


def build_lifecycle_entry(
    *,
    stage_name: str,
    started_at: datetime,
    completed_at: datetime,
    status: str,
    summary: str,
    confidence: float | None = None,
    request_id: str | None = None,
    trace_id: str | None = None,
    runtime_version: str | None = None,
    input_snapshot: dict[str, Any] | None = None,
    output_snapshot: dict[str, Any] | None = None,
    warnings: tuple[str, ...] = (),
    errors: tuple[str, ...] = (),
) -> RuntimeLifecycleEntry:
    return RuntimeLifecycleEntry(
        stage_name=stage_name,
        started_at=started_at.isoformat(),
        completed_at=completed_at.isoformat(),
        duration=(completed_at - started_at).total_seconds(),
        status=status,
        summary=summary,
        confidence=confidence,
        request_id=request_id,
        trace_id=trace_id,
        runtime_version=runtime_version,
        input_snapshot=input_snapshot,
        output_snapshot=output_snapshot,
        warnings=warnings,
        errors=errors,
    )


class ExecutionStateMachine:
    _allowed_transitions = {
        ExecutionState.INITIALIZED: {ExecutionState.READY, ExecutionState.CANCELLED, ExecutionState.FAILED},
        ExecutionState.READY: {ExecutionState.RUNNING, ExecutionState.CANCELLED, ExecutionState.FAILED},
        ExecutionState.RUNNING: {ExecutionState.WAITING, ExecutionState.COMPLETED, ExecutionState.FAILED, ExecutionState.CANCELLED},
        ExecutionState.WAITING: {ExecutionState.RUNNING, ExecutionState.FAILED, ExecutionState.CANCELLED},
        ExecutionState.COMPLETED: set(),
        ExecutionState.FAILED: set(),
        ExecutionState.CANCELLED: set(),
    }

    def __init__(self, initial_state: ExecutionState = ExecutionState.INITIALIZED) -> None:
        self.current_state = initial_state
        self.transitions: list[ExecutionStateTransition] = [
            ExecutionStateTransition(
                from_state=None,
                to_state=initial_state,
                timestamp=datetime.now(timezone.utc).isoformat(),
                summary="Execution initialized.",
            )
        ]

    def transition_to(self, state: ExecutionState, *, task_id: str | None = None, summary: str = "") -> ExecutionStateTransition:
        if state not in self._allowed_transitions[self.current_state]:
            raise ValueError(f"Invalid execution state transition: {self.current_state.value} -> {state.value}")
        transition = ExecutionStateTransition(
            from_state=self.current_state,
            to_state=state,
            timestamp=datetime.now(timezone.utc).isoformat(),
            task_id=task_id,
            summary=summary,
        )
        self.current_state = state
        self.transitions.append(transition)
        return transition


def build_execution_tasks(blueprint: ExecutionBlueprint) -> tuple[ExecutionTask, ...]:
    priorities = {task_id: index for index, task_id in enumerate(blueprint.priority_ordering)}
    dependency_chain: dict[str, tuple[str, ...]] = {}

    capability_names = tuple(blueprint.required_runtime_capabilities)
    if capability_names:
        tasks: list[ExecutionTask] = []
        for index, capability_name in enumerate(capability_names):
            task_id = f"capability_{index + 1}"
            dependency_chain[task_id] = (f"capability_{index}",) if index > 0 else ()
            tasks.append(
                ExecutionTask(
                    task_id=task_id,
                    title=f"Execute {capability_name} capability",
                    description=f"Invoke the {capability_name} runtime executor.",
                    required_capability=capability_name.lower(),
                    current_state=ExecutionState.READY,
                    dependencies=dependency_chain[task_id],
                    priority=priorities.get(task_id, index),
                    execution_metadata={
                        "capability_name": capability_name,
                        "source": "required_runtime_capabilities",
                    },
                )
            )
        if not any(task.required_capability == "provider" for task in tasks):
            task_id = "capability_provider"
            dependency_chain[task_id] = (tasks[-1].task_id,) if tasks else ()
            tasks.append(
                ExecutionTask(
                    task_id=task_id,
                    title="Execute Provider capability",
                    description="Invoke the provider runtime executor.",
                    required_capability="provider",
                    current_state=ExecutionState.READY,
                    dependencies=dependency_chain[task_id],
                    priority=priorities.get(task_id, len(tasks)),
                    execution_metadata={
                        "capability_name": "Provider",
                        "source": "final_response",
                    },
                )
            )
        return tuple(tasks)

    dependencies: dict[str, list[str]] = {}
    for edge in blueprint.dependency_graph:
        dependencies.setdefault(edge.target, []).append(edge.source)

    tasks: list[ExecutionTask] = []
    for index, planned_task in enumerate(blueprint.task_graph):
        required_capability = planned_task.required_capabilities[0] if planned_task.required_capabilities else "runtime_v1"
        tasks.append(
            ExecutionTask(
                task_id=planned_task.identifier,
                title=planned_task.title,
                description=planned_task.description,
                required_capability=required_capability,
                current_state=ExecutionState.READY,
                dependencies=tuple(dependencies.get(planned_task.identifier, ())),
                priority=priorities.get(planned_task.identifier, index),
                execution_metadata={
                    "expected_output": planned_task.expected_output,
                    "estimated_complexity": planned_task.estimated_complexity,
                    "estimated_confidence": planned_task.estimated_confidence,
                },
            )
        )
    return tuple(sorted(tasks, key=lambda task: task.priority))
