"""
Runtime V2 autonomous execution engine.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from app.observability.diagnostics import register_task_report, register_task_trace
from app.runtime.goal_management import GoalLifecycleState, GoalPriority, GoalReport
from app.runtime.task_management import TaskLifecycleState, TaskManager, TaskQueue, TaskQueueSnapshot, TaskReport
from app.observability.diagnostics import register_autonomous_execution


class ExecutionDecision(str, Enum):
    EXECUTABLE = "executable"
    BLOCKED = "blocked"
    WAITING = "waiting"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class ExecutionPolicyDecision:
    decision: ExecutionDecision
    reason: str


@dataclass(frozen=True)
class AutonomousExecutionReport:
    goal: GoalReport
    tasks: tuple[TaskReport, ...]
    completed_tasks: tuple[TaskReport, ...]
    failed_tasks: tuple[TaskReport, ...]
    blocked_tasks: tuple[TaskReport, ...]
    queue_snapshot: TaskQueueSnapshot
    progress_percent: float
    started_at: str
    completed_at: str
    duration: float
    summary: str
    metadata: dict[str, Any]


class ExecutionPolicy:
    def decide(self, *, task: TaskReport, completed_task_ids: set[str]) -> ExecutionPolicyDecision:
        if task.status == TaskLifecycleState.CANCELLED:
            return ExecutionPolicyDecision(ExecutionDecision.CANCELLED, "Task is cancelled.")
        if task.status == TaskLifecycleState.COMPLETED:
            return ExecutionPolicyDecision(ExecutionDecision.SKIPPED, "Task already completed.")
        if not TaskManager().validate_dependencies(task, completed_task_ids):
            return ExecutionPolicyDecision(ExecutionDecision.BLOCKED, "Dependencies are not satisfied.")
        if task.status == TaskLifecycleState.READY:
            return ExecutionPolicyDecision(ExecutionDecision.EXECUTABLE, "Task is ready for execution.")
        return ExecutionPolicyDecision(ExecutionDecision.WAITING, "Task is waiting for readiness.")


class AutonomousExecutionEngine:
    def __init__(self, runtime_v2: Any, task_manager: TaskManager | None = None, execution_policy: ExecutionPolicy | None = None) -> None:
        self.runtime_v2 = runtime_v2
        self.task_manager = task_manager or TaskManager()
        self.execution_policy = execution_policy or ExecutionPolicy()

    async def execute_goal(self, *, goal: GoalReport, current_user: Any, organization_id: int) -> AutonomousExecutionReport:
        started_at = datetime.now(timezone.utc)
        tasks = self.task_manager.prioritize_tasks(self.task_manager.split_goal(goal))
        queue = TaskQueue()
        for task in tasks:
            queue.enqueue(task)
        execution_id = str(goal.goal_id or "goal")
        await register_autonomous_execution(execution_id, {"status": "running", "goal_id": goal.goal_id, "task_count": len(tasks)})
        await register_task_trace(execution_id, {"stage_name": "Loop Started", "goal_id": goal.goal_id, "status": goal.status.value})
        completed_tasks: list[TaskReport] = []
        failed_tasks: list[TaskReport] = []
        blocked_tasks: list[TaskReport] = []
        completed_ids: set[str] = set()
        loop_tasks: list[TaskReport] = list(tasks)

        while True:
            ready = self.task_manager.ready_tasks(tuple(loop_tasks))
            if not ready:
                break
            active_task = ready[0]
            decision = self.execution_policy.decide(task=active_task, completed_task_ids=completed_ids)
            await register_task_report(active_task.task_id or "task", {"task_id": active_task.task_id, "decision": decision.decision.value, "reason": decision.reason, "status": active_task.status.value})
            if decision.decision != ExecutionDecision.EXECUTABLE:
                if decision.decision == ExecutionDecision.BLOCKED:
                    blocked_tasks.append(active_task)
                    loop_tasks = [self.task_manager.update_task(task, status=TaskLifecycleState.BLOCKED) if task.task_id == active_task.task_id else task for task in loop_tasks]
                elif decision.decision == ExecutionDecision.CANCELLED:
                    loop_tasks = [self.task_manager.cancel_task(task) if task.task_id == active_task.task_id else task for task in loop_tasks]
                else:
                    loop_tasks = [self.task_manager.update_task(task, status=TaskLifecycleState.WAITING) if task.task_id == active_task.task_id else task for task in loop_tasks]
                continue

            reserved = self.task_manager.update_task(active_task, status=TaskLifecycleState.RUNNING)
            await register_task_trace(execution_id, {"stage_name": "Task Reserved", "task_id": reserved.task_id, "goal_id": goal.goal_id})
            await register_task_trace(execution_id, {"stage_name": "Task Executing", "task_id": reserved.task_id, "goal_id": goal.goal_id})
            payload = type("TaskPayload", (), {"message": reserved.description or reserved.title, "runtime_version": "AgentCorp V2"})()
            try:
                await self.runtime_v2.execute_chat(payload=payload, current_user=current_user, organization_id=organization_id)
                finished = self.task_manager.complete_task(reserved)
                completed_tasks.append(finished)
                completed_ids.add(finished.task_id or "")
                loop_tasks = [finished if task.task_id == finished.task_id else task for task in loop_tasks]
                await register_task_trace(execution_id, {"stage_name": "Task Finished", "task_id": finished.task_id, "goal_id": goal.goal_id, "status": finished.status.value})
            except Exception as exc:  # deterministic failure handling
                failed = self.task_manager.update_task(reserved, status=TaskLifecycleState.FAILED, metadata={"error": str(exc)})
                failed_tasks.append(failed)
                loop_tasks = [failed if task.task_id == failed.task_id else task for task in loop_tasks]
                await register_task_trace(execution_id, {"stage_name": "Task Finished", "task_id": failed.task_id, "goal_id": goal.goal_id, "status": failed.status.value, "error": str(exc)})
            await register_task_trace(execution_id, {"stage_name": "Queue Updated", "goal_id": goal.goal_id, "queue_size": len(loop_tasks)})

        queue_snapshot = self.task_manager.queue_snapshot(tuple(loop_tasks))
        completed_at = datetime.now(timezone.utc)
        goal_status = GoalLifecycleState.COMPLETED if len(failed_tasks) == 0 and len(blocked_tasks) == 0 and len(completed_tasks) == len(tasks) else GoalLifecycleState.ACTIVE
        updated_goal = replace(goal, status=goal_status, completed_at=completed_at.isoformat() if goal_status == GoalLifecycleState.COMPLETED else goal.completed_at)
        await register_task_trace(execution_id, {"stage_name": "Loop Finished", "goal_id": goal.goal_id, "status": goal_status.value})
        await register_autonomous_execution(execution_id, {
            "status": "completed",
            "goal_id": goal.goal_id,
            "task_count": len(tasks),
            "completed_count": len(completed_tasks),
            "failed_count": len(failed_tasks),
            "blocked_count": len(blocked_tasks),
            "progress_percent": round((len(completed_tasks) / len(tasks)) * 100 if tasks else 100.0, 2),
        })
        return AutonomousExecutionReport(
            goal=updated_goal,
            tasks=tuple(loop_tasks),
            completed_tasks=tuple(completed_tasks),
            failed_tasks=tuple(failed_tasks),
            blocked_tasks=tuple(blocked_tasks),
            queue_snapshot=queue_snapshot,
            progress_percent=round((len(completed_tasks) / len(tasks)) * 100 if tasks else 100.0, 2),
            started_at=started_at.isoformat(),
            completed_at=completed_at.isoformat(),
            duration=(completed_at - started_at).total_seconds(),
            summary=f"Executed {len(completed_tasks)} task(s) with {len(failed_tasks)} failure(s).",
            metadata={"goal_id": goal.goal_id, "organization_id": organization_id, "task_count": len(tasks)},
        )
