from __future__ import annotations

import asyncio

from app.models.goal import Goal
from app.observability.diagnostics import register_goal_report, register_goal_trace
from app.runtime.goal_management import (
    GoalEngine,
    GoalLifecycleState,
    GoalLink,
    GoalMilestone,
    GoalPriority,
)
from app.services.observability_service import ObservabilityService


def test_goal_engine_creates_structured_goal_report() -> None:
    report = GoalEngine().create_goal(
        title="Ship onboarding flow",
        objective="Deliver a stable onboarding flow for new users.",
        owner_id=7,
        organization_id=11,
        description="Coordinate the release.",
        priority=GoalPriority.HIGH,
        dependencies=(GoalLink(goal_id=101, relation="dependency"),),
        metadata={"source": "manual"},
    )
    assert report.title == "Ship onboarding flow"
    assert report.status == GoalLifecycleState.CREATED
    assert report.dependencies[0].goal_id == 101
    assert report.metadata["source"] == "manual"


def test_goal_engine_lifecycle_transitions_and_milestones() -> None:
    engine = GoalEngine()
    report = engine.create_goal(
        title="Draft migration plan",
        objective="Prepare a phased migration plan.",
        owner_id=1,
        organization_id=2,
    )
    report = engine.update_goal(report, status=GoalLifecycleState.ANALYZED)
    report = engine.track_milestone(report, GoalMilestone("Outline", "Create outline", True))
    report = engine.update_goal(report, status=GoalLifecycleState.READY)
    closed = engine.close_goal(report)
    assert closed.status == GoalLifecycleState.COMPLETED
    assert closed.completed_at is not None
    assert closed.milestones[0].title == "Outline"


def test_goal_engine_dependency_validation_and_priority_ordering() -> None:
    engine = GoalEngine()
    urgent = engine.create_goal(title="Urgent", objective="Urgent", owner_id=1, organization_id=1, priority=GoalPriority.URGENT)
    low = engine.create_goal(title="Low", objective="Low", owner_id=1, organization_id=1, priority=GoalPriority.LOW)
    blocked = engine.create_goal(title="Blocked", objective="Blocked", owner_id=1, organization_id=1, dependencies=(GoalLink(goal_id=999, relation="dependency"),))
    ordered = engine.prioritize_goals((low, urgent))
    assert ordered[0].priority == GoalPriority.URGENT
    assert engine.validate_dependencies(blocked, {1, 2, 3}) is False
    assert engine.validate_dependencies(urgent, {1, 2, 3}) is True


def test_goal_engine_from_db_maps_existing_goal_model() -> None:
    goal = Goal(
        organization_id=10,
        agent_id=3,
        conversation_id=None,
        title="Existing goal",
        description="From db",
        objective="Keep compatibility",
        priority="high",
        status="READY",
        constraints={"limit": 1},
        success_criteria="Done",
        created_by=42,
    )
    goal.id = 55
    report = GoalEngine.from_db(goal, child_goal_ids=(2, 3), dependency_ids=(8,))
    assert report.goal_id == 55
    assert report.priority == GoalPriority.HIGH
    assert report.status == GoalLifecycleState.READY
    assert report.dependencies[0].goal_id == 8
    assert report.metadata["success_criteria"] == "Done"


def test_goal_observability_snapshot_includes_goal_reports_and_trace() -> None:
    asyncio.run(register_goal_report("goal-1", {"goal_id": "goal-1", "goal_status": "READY", "priority": "high"}))
    asyncio.run(register_goal_trace("goal-1", {"stage_name": "Goal Ready", "goal_id": "goal-1"}))
    service = ObservabilityService.__new__(ObservabilityService)
    diagnostics = asyncio.run(service.get_diagnostics())
    assert diagnostics["last_goal_report"]["goal_status"] == "READY"
    assert diagnostics["last_goal_trace"]["stage_name"] == "Goal Ready"


def test_goal_runtime_observatory_surfaces_goal_layer() -> None:
    service = ObservabilityService.__new__(ObservabilityService)

    async def fake_get_diagnostics():
        return {
            "last_goal_report": {"goal_id": "goal-2", "goal_status": "ACTIVE", "priority": "medium"},
            "active_goal_reports": [{"goal_id": "goal-2", "goal_status": "ACTIVE", "priority": "medium"}],
            "last_goal_trace": {"stage_name": "Goal Active", "goal_id": "goal-2"},
            "active_goal_traces": [{"stage_name": "Goal Active", "goal_id": "goal-2"}],
        }

    async def fake_get_traces():
        return []

    service.get_diagnostics = fake_get_diagnostics  # type: ignore[method-assign]
    service.get_active_traces = fake_get_traces  # type: ignore[method-assign]
    observatory = asyncio.run(service.get_runtime_observatory())
    assert observatory["goal_report"]["goal_status"] == "ACTIVE"
    assert observatory["goal_trace"]["stage_name"] == "Goal Active"
