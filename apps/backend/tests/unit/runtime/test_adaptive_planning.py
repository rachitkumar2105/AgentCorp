"""Unit tests for adaptive planning."""

from __future__ import annotations

from dataclasses import replace

from app.runtime.adaptive_planning import AdaptivePlanningEngine, ReplanningPolicy
from app.runtime.cognitive import CognitiveEngine
from app.runtime.evaluation import EvaluationEngine
from app.runtime.goal_management import GoalEngine, GoalLifecycleState
from app.runtime.learning import LearningEngine
from app.runtime.planning import PlanningEngine
from app.runtime.reflection import ReflectionEngine
from app.runtime.execution import create_execution_context
from app.runtime.router import RuntimeVersion


def _build_reports(message: str):
    cognitive_state = CognitiveEngine().analyze(
        request_text=message,
        runtime_version=RuntimeVersion.V2.value,
        request_id="adaptive-req",
    )
    blueprint = PlanningEngine().plan(
        cognitive_state=cognitive_state,
        runtime_version=RuntimeVersion.V2.value,
        request_id="adaptive-req",
    )
    context = create_execution_context(
        original_request={"message": message},
        runtime_version=RuntimeVersion.V2.value,
        request_id="adaptive-req",
    ).with_updates(cognitive_state=cognitive_state, execution_blueprint=blueprint)
    execution_result = type(
        "ExecutionResult",
        (),
        {
            "task_id": "task_1",
            "status": type("Status", (), {"value": "FAILED"})(),
            "outputs": {},
            "errors": ("missing dependency",),
            "duration": 0.5,
            "metadata": {"required_capability": "provider"},
        },
    )()
    reflection_report = ReflectionEngine().reflect(
        execution_context=context,
        execution_result=execution_result,
        execution_trace=context.execution_trace,
    )
    evaluation_report = EvaluationEngine().evaluate(
        execution_context=context,
        execution_result=execution_result,
        reflection_report=reflection_report,
    )
    learning_report = LearningEngine().learn(
        execution_context=context,
        reflection_report=reflection_report,
        evaluation_report=evaluation_report,
        execution_trace=context.execution_trace,
    )
    goal = GoalEngine().create_goal(
        title="Adaptive goal",
        objective=message,
        owner_id=1,
        organization_id=1,
    )
    return goal, blueprint, reflection_report, evaluation_report, learning_report


def test_replanning_policy_is_deterministic() -> None:
    goal, blueprint, reflection_report, evaluation_report, learning_report = _build_reports(
        "Build a backend plan with missing details and a blocked dependency."
    )
    policy = ReplanningPolicy()
    first = policy.should_replan(
        reflection_report=reflection_report,
        evaluation_report=evaluation_report,
        learning_report=learning_report,
        goal=replace(goal, status=GoalLifecycleState.ACTIVE),
        blueprint=blueprint,
    )
    second = policy.should_replan(
        reflection_report=reflection_report,
        evaluation_report=evaluation_report,
        learning_report=learning_report,
        goal=replace(goal, status=GoalLifecycleState.ACTIVE),
        blueprint=blueprint,
    )

    assert first == second
    assert first[0] is True
    assert "goal_incomplete" in first[1]


def test_adaptive_planning_engine_revises_blueprint_and_preserves_work() -> None:
    goal, blueprint, reflection_report, evaluation_report, learning_report = _build_reports(
        "Build a backend plan with missing details and a blocked dependency."
    )
    report = AdaptivePlanningEngine(PlanningEngine()).revise_blueprint(
        goal=replace(goal, status=GoalLifecycleState.ACTIVE),
        previous_blueprint=blueprint,
        reflection_report=reflection_report,
        evaluation_report=evaluation_report,
        learning_report=learning_report,
    )

    assert report.replanning_required is True
    assert report.revision_number == 2
    assert report.revised_blueprint.revision_number == 2
    assert report.revised_blueprint.planning_rationale == report.replanning_reason
    assert report.revised_blueprint.blueprint_history
    assert report.plan_diff.added_tasks
    assert report.plan_diff.removed_tasks
    assert any(task.identifier == "task_1" for task in report.revised_blueprint.task_graph)
    assert report.trace[0]["stage_name"] == "Replanning Started"
    assert report.trace[-1]["stage_name"] == "Replanning Completed"
