"""Unit tests for the multi-agent orchestration layer."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from app.multi_agent.orchestrator import MultiAgentOrchestrator, ResultAggregator
from app.observability import diagnostics
from app.runtime.goal_management import GoalEngine, GoalPriority
from app.runtime.task_management import TaskLifecycleState, TaskManager
from app.runtime.autonomous_execution import AutonomousExecutionReport


class _FakeRuntime:
    async def execute_chat(self, payload, current_user, organization_id):  # pragma: no cover - exercised through orchestrator
        return {
            "message": payload.message,
            "organization_id": organization_id,
            "user_id": getattr(current_user, "id", None),
        }


class _FakeMultiAgentService:
    pass


@pytest.mark.anyio
async def test_orchestrator_routes_task_delegation_and_aggregation(monkeypatch):
    captured_events: list[tuple[int, dict]] = []

    async def fake_publish(session_id: int, message: dict) -> None:
        captured_events.append((session_id, message))

    async def fake_register(execution_id: str, metadata: dict) -> None:
        diagnostics.active_autonomous_executions[execution_id] = metadata
        diagnostics.last_autonomous_execution = metadata

    async def fake_execute_goal(self, *, goal, current_user, organization_id):
        task_manager = TaskManager()
        tasks = task_manager.split_goal(goal)
        completed = tuple(task_manager.complete_task(task) for task in tasks)
        report = AutonomousExecutionReport(
            goal=goal,
            tasks=completed,
            completed_tasks=completed,
            failed_tasks=(),
            blocked_tasks=(),
            queue_snapshot=task_manager.queue_snapshot(completed),
            progress_percent=100.0,
            started_at=goal.created_at,
            completed_at=goal.updated_at,
            duration=0.25,
            summary="Executed all delegated tasks.",
            metadata={"goal_id": goal.goal_id, "organization_id": organization_id},
        )
        return report

    monkeypatch.setattr("app.multi_agent.orchestrator.message_bus.publish", fake_publish)
    monkeypatch.setattr("app.multi_agent.orchestrator.register_autonomous_execution", fake_register)
    monkeypatch.setattr("app.multi_agent.orchestrator.AutonomousExecutionEngine.execute_goal", fake_execute_goal)

    goal = GoalEngine().create_goal(
        title="Launch campaign",
        objective="Draft positioning, review messaging, and publish assets.",
        owner_id=7,
        organization_id=99,
        metadata={"deadline": "2026-08-10T00:00:00+05:30"},
    )
    orchestrator = MultiAgentOrchestrator(runtime_v2=_FakeRuntime(), multi_agent_service=_FakeMultiAgentService())
    report = await orchestrator.orchestrate_goal(
        goal=goal,
        supervisor_agent_id=101,
        worker_agent_ids=(201, 202),
        current_user=SimpleNamespace(id=7),
        organization_id=99,
        session_id=55,
    )

    assert report.supervisor_agent_id == 101
    assert report.shared_context.participating_agents == (101, 201, 202)
    assert report.shared_context.delegated_tasks
    assert report.aggregation_summary == "Executed all delegated tasks."
    assert report.metadata["worker_agent_count"] == 2
    assert captured_events[0][0] == 55
    assert captured_events[0][1]["event"] == "supervisor_started"
    assert captured_events[1][1]["event"] == "task_delegation"
    assert diagnostics.last_autonomous_execution["status"] == "multi_agent_completed"


def test_result_aggregator_includes_execution_provenance():
    goal = GoalEngine().create_goal(
        title="Write brief",
        objective="Create a concise summary with next steps and a rollout plan for stakeholders.",
        owner_id=3,
        organization_id=8,
        priority=GoalPriority.HIGH,
    )
    task_manager = TaskManager()
    tasks = task_manager.split_goal(goal)
    report = AutonomousExecutionReport(
        goal=goal,
        tasks=tasks,
        completed_tasks=tasks[:1],
        failed_tasks=tasks[1:2],
        blocked_tasks=tasks[2:],
        queue_snapshot=task_manager.queue_snapshot(tasks),
        progress_percent=33.33,
        started_at=goal.created_at,
        completed_at=goal.updated_at,
        duration=1.0,
        summary="Partial execution with one failure.",
        metadata={"goal_id": goal.goal_id, "organization_id": 8},
    )

    aggregated = ResultAggregator().aggregate(report)

    assert aggregated["goal_id"] == goal.goal_id
    assert aggregated["completed_tasks"] == [tasks[0].task_id]
    assert aggregated["failed_tasks"] == [tasks[1].task_id]
    assert aggregated["blocked_tasks"] == [tasks[2].task_id]
    assert aggregated["progress_percent"] == 33.33
    assert aggregated["provenance"]["organization_id"] == 8
