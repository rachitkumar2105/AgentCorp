from __future__ import annotations

import asyncio

from app.models.goal import Goal
from app.observability.diagnostics import register_autonomous_execution
from app.runtime.autonomous_execution import AutonomousExecutionEngine, ExecutionDecision, ExecutionPolicy
from app.runtime.goal_management import GoalEngine, GoalLifecycleState, GoalPriority
from app.runtime.task_management import TaskLifecycleState, TaskManager
from app.services.observability_service import ObservabilityService


def _build_goal_report():
    goal = Goal(
        organization_id=1,
        agent_id=1,
        conversation_id=None,
        title="Ship docs",
        description="Ship docs",
        objective="Plan docs release now",
        priority="high",
        status="READY",
        constraints={},
        success_criteria="Done",
        created_by=1,
    )
    goal.id = 22
    return GoalEngine.from_db(goal)


def test_execution_policy_is_deterministic() -> None:
    goal = _build_goal_report()
    task = TaskManager().split_goal(goal)[0]
    decision = ExecutionPolicy().decide(task=task, completed_task_ids=set())
    assert decision.decision == ExecutionDecision.EXECUTABLE


def test_autonomous_execution_loop_runs_and_updates_goal_progress() -> None:
    class DummyRuntime:
        def __init__(self):
            self.calls = 0

        async def execute_chat(self, *, payload, current_user, organization_id, conversation_id=None):
            self.calls += 1
            return {"ok": True}

    goal = _build_goal_report()
    runtime = DummyRuntime()
    engine = AutonomousExecutionEngine(runtime)

    report = asyncio.run(engine.execute_goal(goal=goal, current_user=type("User", (), {"id": 9})(), organization_id=1))
    assert runtime.calls == 1
    assert report.completed_tasks
    assert report.progress_percent == 100.0
    assert report.goal.status == GoalLifecycleState.COMPLETED


def test_autonomous_execution_registers_observability() -> None:
    asyncio.run(register_autonomous_execution("22", {"status": "running", "goal_id": 22}))
    diagnostics = asyncio.run(ObservabilityService.__new__(ObservabilityService).get_diagnostics())
    assert diagnostics["last_autonomous_execution"]["goal_id"] == 22


def test_runtime_observatory_surfaces_autonomous_execution() -> None:
    service = ObservabilityService.__new__(ObservabilityService)

    async def fake_get_diagnostics():
        return {
            "last_autonomous_execution": {"goal_id": 22, "status": "completed"},
            "active_autonomous_executions": [{"goal_id": 22, "status": "completed"}],
        }

    async def fake_get_traces():
        return []

    service.get_diagnostics = fake_get_diagnostics  # type: ignore[method-assign]
    service.get_active_traces = fake_get_traces  # type: ignore[method-assign]
    observatory = asyncio.run(service.get_runtime_observatory())
    assert observatory["autonomous_execution"]["goal_id"] == 22
