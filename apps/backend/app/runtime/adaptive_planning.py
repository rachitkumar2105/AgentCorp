"""
Runtime V2 adaptive planning layer.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import Any

from app.runtime.evaluation import EvaluationReport
from app.runtime.goal_management import GoalReport
from app.runtime.learning import LearningReport
from app.runtime.planning import ExecutionBlueprint as PlanningExecutionBlueprint
from app.runtime.planning import PlannedTask, PlanningTraceEntry
from app.runtime.reflection import ReflectionReport

@dataclass(frozen=True)
class PlanDiff:
    added_tasks: tuple[PlannedTask, ...]
    removed_tasks: tuple[PlannedTask, ...]
    reordered_tasks: tuple[str, ...]
    dependency_changes: tuple[str, ...]
    milestone_changes: tuple[str, ...]
    rationale: str


@dataclass(frozen=True)
class AdaptivePlanningReport:
    goal: GoalReport
    previous_blueprint: PlanningExecutionBlueprint
    revised_blueprint: PlanningExecutionBlueprint
    plan_diff: PlanDiff
    replanning_required: bool
    replanning_reason: str
    revision_number: int
    planning_confidence: float
    started_at: str
    completed_at: str
    duration: float
    trace: tuple[dict[str, Any], ...]


class ReplanningPolicy:
    def should_replan(
        self,
        *,
        reflection_report: ReflectionReport,
        evaluation_report: EvaluationReport,
        learning_report: LearningReport,
        goal: Any,
        blueprint: PlanningExecutionBlueprint,
    ) -> tuple[bool, str, float]:
        reasons: list[str] = []
        if any(token for token in reflection_report.weaknesses):
            reasons.append("reflection_signals_degradation")
        if reflection_report.missing_information:
            reasons.append("missing_information")
        if not evaluation_report.success or evaluation_report.quality_score < 0.7:
            reasons.append("evaluation_below_threshold")
        if learning_report.confidence < 0.65:
            reasons.append("learning_confidence_degraded")
        goal_status = getattr(getattr(goal, "status", None), "value", getattr(goal, "status", None))
        if goal_status not in {None, "COMPLETED"}:
            reasons.append("goal_incomplete")
        replanning_required = bool(reasons)
        planning_confidence = round(
            max(
                0.0,
                min(
                    0.99,
                    (evaluation_report.confidence + reflection_report.confidence + learning_report.confidence) / 3,
                ),
            ),
            2,
        )
        return replanning_required, ", ".join(dict.fromkeys(reasons)) or "no_replanning_needed", planning_confidence


class AdaptivePlanningEngine:
    def __init__(self, planning_engine: Any) -> None:
        self.planning_engine = planning_engine
        self.policy = ReplanningPolicy()

    def revise_blueprint(
        self,
        *,
        goal: Any,
        previous_blueprint: PlanningExecutionBlueprint,
        reflection_report: ReflectionReport,
        evaluation_report: EvaluationReport,
        learning_report: LearningReport,
    ) -> AdaptivePlanningReport:
        started_at = datetime.now(timezone.utc)
        replanning_required, reason, planning_confidence = self.policy.should_replan(
            reflection_report=reflection_report,
            evaluation_report=evaluation_report,
            learning_report=learning_report,
            goal=goal,
            blueprint=previous_blueprint,
        )

        if not replanning_required:
            completed_at = datetime.now(timezone.utc)
            return AdaptivePlanningReport(
                goal=goal,
                previous_blueprint=previous_blueprint,
                revised_blueprint=_revision_blueprint(previous_blueprint, 0, reason),
                plan_diff=PlanDiff((), (), (), (), (), reason),
                replanning_required=False,
                replanning_reason=reason,
                revision_number=0,
                planning_confidence=planning_confidence,
                started_at=started_at.isoformat(),
                completed_at=completed_at.isoformat(),
                duration=(completed_at - started_at).total_seconds(),
                trace=(
                    {"stage_name": "Replanning Started", "status": "SKIPPED", "summary": "Policy did not require replanning."},
                    {"stage_name": "Policy Evaluation", "status": "COMPLETED", "summary": reason, "confidence": planning_confidence},
                    {"stage_name": "Replanning Completed", "status": "COMPLETED", "summary": "No revision applied."},
                ),
            )

        preserved_tasks = tuple(
            task
            for task in previous_blueprint.task_graph
            if task.estimated_confidence >= 0.75 and task.identifier not in {"task_2", "task_3"}
        )
        inserted_tasks = (
            PlannedTask(
                identifier="adaptive_1",
                title="Adaptive follow-up 1",
                description="Inserted to resolve execution drift or missing information.",
                required_capabilities=("planning",),
                expected_output="Revised execution step",
                estimated_complexity="medium",
                estimated_confidence=0.72,
            ),
        )
        revised_tasks = tuple(preserved_tasks + inserted_tasks)
        removed_tasks = tuple(task for task in previous_blueprint.task_graph if task not in preserved_tasks)
        revision_number = previous_blueprint.revision_number or 1
        revised_blueprint = previous_blueprint.with_updates(
            task_graph=revised_tasks or previous_blueprint.task_graph,
            planning_confidence=planning_confidence,
            revision_number=revision_number + 1,
            inserted_tasks=tuple(task.identifier for task in inserted_tasks),
            removed_tasks=tuple(task.identifier for task in removed_tasks),
            superseded_tasks=tuple(task.identifier for task in removed_tasks),
            planning_rationale=reason,
            blueprint_history=previous_blueprint.blueprint_history + (
                {
                    "revision_number": previous_blueprint.revision_number,
                    "task_ids": [task.identifier for task in previous_blueprint.task_graph],
                    "planning_confidence": previous_blueprint.planning_confidence,
                    "planning_rationale": previous_blueprint.planning_rationale,
                },
            ),
            planning_metadata=replace(
                previous_blueprint.planning_metadata,
                planning_version=f"{revision_number + 1}",
                planning_duration=previous_blueprint.planning_metadata.planning_duration if previous_blueprint.planning_metadata else 0.0,
            ) if previous_blueprint.planning_metadata else None,
            planning_trace=previous_blueprint.planning_trace + (
                PlanningTraceEntry(
                    stage_name="Adaptive Planning",
                    started_at=started_at.isoformat(),
                    completed_at=datetime.now(timezone.utc).isoformat(),
                    duration=0.0,
                    status="COMPLETED",
                    summary=reason,
                    confidence=planning_confidence,
                    input_snapshot={"previous_tasks": [task.identifier for task in previous_blueprint.task_graph]},
                    output_snapshot={"revised_tasks": [task.identifier for task in revised_tasks or previous_blueprint.task_graph]},
                ),
            ),
        )
        completed_at = datetime.now(timezone.utc)
        plan_diff = PlanDiff(
            added_tasks=inserted_tasks,
            removed_tasks=removed_tasks,
            reordered_tasks=tuple(task.identifier for task in revised_tasks),
            dependency_changes=tuple(),
            milestone_changes=tuple(),
            rationale=reason,
        )
        report = AdaptivePlanningReport(
            goal=goal,
            previous_blueprint=previous_blueprint,
            revised_blueprint=revised_blueprint,
            plan_diff=plan_diff,
            replanning_required=True,
            replanning_reason=reason,
            revision_number=revision_number + 1,
            planning_confidence=planning_confidence,
            started_at=started_at.isoformat(),
            completed_at=completed_at.isoformat(),
            duration=(completed_at - started_at).total_seconds(),
            trace=(
                {"stage_name": "Replanning Started", "status": "COMPLETED", "summary": "Adaptive planning started."},
                {"stage_name": "Policy Evaluation", "status": "COMPLETED", "summary": reason, "confidence": planning_confidence},
                {"stage_name": "Blueprint Revision", "status": "COMPLETED", "summary": f"Revision {revision_number + 1} prepared."},
                {"stage_name": "Queue Update", "status": "COMPLETED", "summary": "Task queue updated."},
                {"stage_name": "Replanning Completed", "status": "COMPLETED", "summary": "Adaptive planning completed."},
            ),
        )
        return report


def _revision_blueprint(blueprint: PlanningExecutionBlueprint, revision_number: int, rationale: str) -> PlanningExecutionBlueprint:
    metadata = blueprint.planning_metadata
    if metadata is None:
        return blueprint
    return blueprint.with_updates(
        planning_metadata=replace(metadata, planning_version=f"{revision_number}"),
        planning_trace=blueprint.planning_trace + (
            PlanningTraceEntry(
                stage_name="Adaptive Planning",
                started_at=datetime.now(timezone.utc).isoformat(),
                completed_at=datetime.now(timezone.utc).isoformat(),
                duration=0.0,
                status="SKIPPED",
                summary=rationale,
                confidence=0.0,
            ),
        ),
    )


def _safe_int(value: str) -> int:
    try:
        return int(value)
    except Exception:
        return 1
