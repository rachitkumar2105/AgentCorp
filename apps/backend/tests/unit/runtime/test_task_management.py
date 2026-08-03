from __future__ import annotations

import asyncio

from app.models.goal import Goal
from app.observability.diagnostics import register_task_report, register_task_trace
from app.runtime.goal_management import GoalEngine, GoalPriority
from app.runtime.task_management import (
    TaskLifecycleState,
    TaskManager,
    TaskQueue,
)
from app.services.observability_service import ObservabilityService


def _build_goal_report():
    goal = Goal(
        organization_id=1,
        agent_id=1,
        conversation_id=None,
        title="Launch feature",
        description="Launch feature safely",
        objective="Design, implement, and validate feature delivery.",
        priority="high",
        status="READY",
        constraints={},
        success_criteria="Complete delivery",
        created_by=1,
    )
    goal.id = 7
    return GoalEngine.from_db(goal)


def test_task_manager_generates_tasks_from_goal() -> None:
    goal = _build_goal_report()
    tasks = TaskManager().split_goal(goal)
    assert tasks
    assert tasks[0].goal_id == 7
    assert tasks[0].status == TaskLifecycleState.READY
    assert tasks[-1].status in {TaskLifecycleState.READY, TaskLifecycleState.BLOCKED}


def test_task_manager_validates_dependencies_and_priority() -> None:
    goal = _build_goal_report()
    tasks = TaskManager().split_goal(goal)
    manager = TaskManager()
    ordered = manager.prioritize_tasks(tasks)
    assert ordered[0].priority == GoalPriority.HIGH
    assert manager.validate_dependencies(ordered[0], set()) is True


def test_task_queue_orders_and_inspects_tasks() -> None:
    goal = _build_goal_report()
    tasks = TaskManager().split_goal(goal)
    queue = TaskQueue()
    for task in tasks:
        queue.enqueue(task)
    snapshot = queue.inspect()
    assert snapshot.queue_size == len(tasks)
    assert snapshot.ready_count >= 1
    assert snapshot.dependency_summary["without_dependencies"] >= 1
    assert queue.dequeue() is not None


def test_task_lifecycle_transitions_are_deterministic() -> None:
    goal = _build_goal_report()
    task = TaskManager().split_goal(goal)[0]
    completed = TaskManager().complete_task(task)
    cancelled = TaskManager().cancel_task(task)
    assert completed.status == TaskLifecycleState.COMPLETED
    assert cancelled.status == TaskLifecycleState.CANCELLED


def test_task_observability_snapshot_includes_task_reports() -> None:
    asyncio.run(register_task_report("task-1", {"task_id": "task-1", "status": "READY", "priority": "high"}))
    asyncio.run(register_task_trace("task-1", {"stage_name": "Task Generation", "task_id": "task-1"}))
    diagnostics = asyncio.run(ObservabilityService.__new__(ObservabilityService).get_diagnostics())
    assert diagnostics["last_task_report"]["status"] == "READY"
    assert diagnostics["last_task_trace"]["stage_name"] == "Task Generation"


def test_runtime_observatory_surfaces_task_layer() -> None:
    service = ObservabilityService.__new__(ObservabilityService)

    async def fake_get_diagnostics():
        return {
            "last_task_report": {"task_id": "task-2", "status": "READY", "priority": "medium"},
            "active_task_reports": [{"task_id": "task-2", "status": "READY", "priority": "medium"}],
            "last_task_trace": {"stage_name": "Queue Update", "task_id": "task-2"},
            "active_task_traces": [{"stage_name": "Queue Update", "task_id": "task-2"}],
        }

    async def fake_get_traces():
        return []

    service.get_diagnostics = fake_get_diagnostics  # type: ignore[method-assign]
    service.get_active_traces = fake_get_traces  # type: ignore[method-assign]
    observatory = asyncio.run(service.get_runtime_observatory())
    assert observatory["task_report"]["task_id"] == "task-2"
    assert observatory["task_trace"]["stage_name"] == "Queue Update"
