"""
Native Execution Engine foundation for Runtime V2.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any

from app.models.user import User
from app.observability.diagnostics import register_execution_engine
from app.runtime.dispatcher import CapabilityDispatcher
from app.runtime.execution import (
    ExecutionContext,
    ExecutionResult,
    ExecutionRun,
    ExecutionState,
    ExecutionStateMachine,
    ExecutionTask,
    build_execution_tasks,
    build_lifecycle_entry,
)
from app.schemas.chat import (
    ChatCreateRequest,
    ChatContinueRequest,
    ChatRegenerateRequest,
    ChatRetryRequest,
    ChatResponseSchema,
    ConversationDetailSchema,
)
from app.schemas.streaming import StreamingChatRequest


class ExecutionEngine:
    """
    Canonical Runtime V2 execution orchestrator.

    It consumes the prepared Execution Context and Execution Blueprint, manages
    task lifecycle, and delegates capability work through the dispatcher.
    """

    def __init__(self, dispatcher: CapabilityDispatcher) -> None:
        self.dispatcher = dispatcher

    async def execute_chat(
        self,
        *,
        execution_context: ExecutionContext,
        payload: ChatCreateRequest | ChatContinueRequest | ChatRegenerateRequest | ChatRetryRequest,
        current_user: User,
        organization_id: int,
        conversation_id: int | None = None,
    ) -> ChatResponseSchema | ConversationDetailSchema:
        run = self._initialize_run(execution_context)
        await self._publish(run)
        task = self._select_dispatch_task(run.tasks, preferred_capability="provider")
        machine = ExecutionStateMachine(run.state)
        machine.transitions.extend(run.transitions[1:])
        machine.transition_to(ExecutionState.RUNNING, task_id=task.task_id, summary="Dispatching task.")
        response, result = await self.dispatcher.dispatch_chat(
            task=task,
            execution_context=execution_context.with_updates(execution_state=ExecutionState.RUNNING.value),
            payload=payload,
            current_user=current_user,
            organization_id=organization_id,
            conversation_id=conversation_id,
        )
        machine.transition_to(ExecutionState.COMPLETED, task_id=task.task_id, summary="Execution completed.")
        completed_task = self._with_task_state(task, ExecutionState.COMPLETED)
        completed_run = ExecutionRun(
            execution_id=run.execution_id,
            state=ExecutionState.COMPLETED,
            tasks=tuple(completed_task if item.task_id == task.task_id else item for item in run.tasks),
            results=(result,),
            transitions=tuple(machine.transitions),
            timeline=run.timeline + (
                build_lifecycle_entry(
                    stage_name="Capability Dispatch",
                    started_at=datetime.fromisoformat(result.started_at),
                    completed_at=datetime.fromisoformat(result.completed_at),
                    status=result.status.value,
                    summary=f"Dispatched {task.task_id} via Runtime V1 adapter.",
                    request_id=execution_context.execution_metadata.request_id if execution_context.execution_metadata else None,
                    trace_id=execution_context.execution_metadata.trace_id if execution_context.execution_metadata else None,
                    runtime_version=execution_context.runtime_version,
                    output_snapshot={"task_id": result.task_id, "status": result.status.value},
                    errors=result.errors,
                ),
            ),
        )
        await self._publish(completed_run)
        return response

    async def execute_stream(
        self,
        *,
        execution_context: ExecutionContext,
        payload: StreamingChatRequest,
        current_user: User,
        organization_id: int,
        conversation_id: int | None = None,
    ) -> AsyncGenerator[str, None]:
        run = self._initialize_run(execution_context)
        task = self._select_dispatch_task(run.tasks, preferred_capability="streaming")
        await self._publish(run)
        async for event in self.dispatcher.dispatch_stream(
            task=task,
            execution_context=execution_context.with_updates(execution_state=ExecutionState.RUNNING.value),
            payload=payload,
            current_user=current_user,
            organization_id=organization_id,
            conversation_id=conversation_id,
        ):
            yield event

    def _initialize_run(self, execution_context: ExecutionContext) -> ExecutionRun:
        if execution_context.execution_metadata is None:
            raise ValueError("Execution metadata is required.")
        if execution_context.execution_blueprint is None:
            raise ValueError("Execution blueprint is required.")

        machine = ExecutionStateMachine()
        tasks = build_execution_tasks(execution_context.execution_blueprint)
        machine.transition_to(ExecutionState.READY, summary="Execution tasks prepared.")
        timeline = execution_context.execution_trace + (
            build_lifecycle_entry(
                stage_name="Execution Initialized",
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
                status=ExecutionState.READY.value,
                summary=f"{len(tasks)} tasks ready.",
                request_id=execution_context.execution_metadata.request_id,
                trace_id=execution_context.execution_metadata.trace_id,
                runtime_version=execution_context.runtime_version,
                output_snapshot={"task_count": len(tasks)},
            ),
        )
        return ExecutionRun(
            execution_id=execution_context.execution_metadata.execution_id,
            state=ExecutionState.READY,
            tasks=tasks,
            results=(),
            transitions=tuple(machine.transitions),
            timeline=timeline,
        )

    def _select_dispatch_task(self, tasks: tuple[ExecutionTask, ...], *, preferred_capability: str | None = None) -> ExecutionTask:
        if not tasks:
            raise ValueError("No execution tasks available.")
        if preferred_capability is not None:
            preferred = next((task for task in tasks if task.required_capability == preferred_capability), None)
            if preferred is not None:
                return preferred
        return tasks[0]

    def _with_task_state(self, task: ExecutionTask, state: ExecutionState) -> ExecutionTask:
        return ExecutionTask(
            task_id=task.task_id,
            title=task.title,
            description=task.description,
            required_capability=task.required_capability,
            current_state=state,
            dependencies=task.dependencies,
            priority=task.priority,
            execution_metadata=task.execution_metadata,
        )

    async def _publish(self, run: ExecutionRun) -> None:
        await register_execution_engine(
            run.execution_id,
            {
                "execution_initialized": True,
                "execution_state": run.state.value,
                "current_task": self._current_task_snapshot(run),
                "completed_tasks": [asdict(task) for task in run.tasks if task.current_state == ExecutionState.COMPLETED],
                "pending_tasks": [asdict(task) for task in run.tasks if task.current_state != ExecutionState.COMPLETED],
                "execution_timeline": [asdict(entry) for entry in run.timeline],
                "execution_results": [asdict(result) for result in run.results],
                "state_transitions": [asdict(transition) for transition in run.transitions],
            },
        )

    def _current_task_snapshot(self, run: ExecutionRun) -> dict[str, Any] | None:
        for task in run.tasks:
            if task.current_state != ExecutionState.COMPLETED:
                return asdict(task)
        return None
