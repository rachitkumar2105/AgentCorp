"""
Strategic planning engine for Runtime V2.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import Any, Protocol
import uuid

from app.runtime.cognitive import CognitiveState, CognitiveIntent


@dataclass(frozen=True)
class PlanningMetadata:
    runtime_version: str
    planning_version: str
    request_id: str
    trace_id: str
    created_at: str
    planning_duration: float = 0.0


@dataclass(frozen=True)
class ExecutionObjective:
    primary_objective: str | None = None
    secondary_objectives: tuple[str, ...] = ()
    expected_deliverables: tuple[str, ...] = ()
    completion_criteria: tuple[str, ...] = ()
    unknown_objectives: tuple[str, ...] = ()


@dataclass(frozen=True)
class PlannedTask:
    identifier: str
    title: str
    description: str
    required_capabilities: tuple[str, ...]
    expected_output: str
    estimated_complexity: str
    estimated_confidence: float


@dataclass(frozen=True)
class DependencyEdge:
    source: str
    target: str
    dependency_type: str


@dataclass(frozen=True)
class PlannedMilestone:
    identifier: str
    objective: str
    tasks: tuple[str, ...]
    completion_conditions: tuple[str, ...]
    expected_outputs: tuple[str, ...]


@dataclass(frozen=True)
class RiskAssessmentItem:
    risk_type: str
    likelihood: str
    impact: str
    confidence: float
    summary: str


@dataclass(frozen=True)
class PlanningTraceEntry:
    stage_name: str
    started_at: str
    completed_at: str
    duration: float
    status: str
    summary: str
    confidence: float
    input_snapshot: dict[str, Any] | None = None
    output_snapshot: dict[str, Any] | None = None


@dataclass(frozen=True)
class ExecutionBlueprint:
    planning_metadata: PlanningMetadata | None = None
    execution_objective: ExecutionObjective | None = None
    milestones: tuple[PlannedMilestone, ...] = ()
    execution_stages: tuple[str, ...] = ()
    task_graph: tuple[PlannedTask, ...] = ()
    dependency_graph: tuple[DependencyEdge, ...] = ()
    priority_ordering: tuple[str, ...] = ()
    estimated_risks: tuple[RiskAssessmentItem, ...] = ()
    expected_deliverables: tuple[str, ...] = ()
    required_runtime_capabilities: tuple[str, ...] = ()
    execution_assumptions: tuple[str, ...] = ()
    planning_confidence: float = 0.0
    planning_trace: tuple[PlanningTraceEntry, ...] = ()
    raw_cognitive_state: CognitiveState | None = None
    revision_number: int = 0
    blueprint_history: tuple[dict[str, Any], ...] = ()
    superseded_tasks: tuple[str, ...] = ()
    inserted_tasks: tuple[str, ...] = ()
    removed_tasks: tuple[str, ...] = ()
    planning_rationale: str | None = None

    def with_updates(self, **kwargs: Any) -> "ExecutionBlueprint":
        return replace(self, **kwargs)


class PlanningStage(Protocol):
    stage_name: str

    def plan(self, blueprint: ExecutionBlueprint, cognitive_state: CognitiveState) -> ExecutionBlueprint:
        ...


class ObjectivePlanner:
    stage_name = "Objective Planning"

    def plan(self, blueprint: ExecutionBlueprint, cognitive_state: CognitiveState) -> ExecutionBlueprint:
        normalized_goal = cognitive_state.normalized_goal or "Unknown objective"
        intents = cognitive_state.intent_collection
        secondary = tuple(_secondary_objectives_from_intents(intents))
        deliverables = tuple(_deliverables_from_goal(normalized_goal))
        completion = tuple(_completion_criteria_from_goal(normalized_goal, deliverables))
        objective = ExecutionObjective(
            primary_objective=normalized_goal,
            secondary_objectives=secondary,
            expected_deliverables=deliverables,
            completion_criteria=completion,
            unknown_objectives=("unknown" if normalized_goal == "Unknown objective" else ""),
        )
        objective = replace(objective, unknown_objectives=tuple(x for x in objective.unknown_objectives if x))
        return blueprint.with_updates(
            execution_objective=objective,
            expected_deliverables=deliverables,
        )


class TaskDecomposer:
    stage_name = "Task Decomposition"

    def plan(self, blueprint: ExecutionBlueprint, cognitive_state: CognitiveState) -> ExecutionBlueprint:
        objective = blueprint.execution_objective.primary_objective if blueprint.execution_objective else (cognitive_state.normalized_goal or "Unknown objective")
        tasks = (
            PlannedTask("task_1", "Prepare request context", f"Review the request and normalize the objective: {objective}", ("analysis",), "Structured request summary", "low", 0.86),
            PlannedTask("task_2", "Identify implementation scope", "Determine the bounded runtime work implied by the request.", ("analysis",), "Scope summary", "medium", 0.8),
            PlannedTask("task_3", "Assemble blueprint", "Compose a structured execution blueprint for later execution phases.", ("planning",), "Execution blueprint", "medium", 0.78),
        )
        return blueprint.with_updates(
            task_graph=tasks,
            execution_stages=("objective_planning", "task_decomposition", "dependency_graph", "milestone_planning", "priority_planning", "risk_assessment", "blueprint_assembly"),
        )


class DependencyBuilder:
    stage_name = "Dependency Graph"

    def plan(self, blueprint: ExecutionBlueprint, cognitive_state: CognitiveState) -> ExecutionBlueprint:
        tasks = blueprint.task_graph
        edges = (
            DependencyEdge(source=tasks[0].identifier, target=tasks[1].identifier, dependency_type="sequential") if len(tasks) >= 2 else None,
            DependencyEdge(source=tasks[1].identifier, target=tasks[2].identifier, dependency_type="sequential") if len(tasks) >= 3 else None,
        )
        filtered = tuple(edge for edge in edges if edge is not None)
        return blueprint.with_updates(dependency_graph=filtered)


class MilestoneBuilder:
    stage_name = "Milestone Planning"

    def plan(self, blueprint: ExecutionBlueprint, cognitive_state: CognitiveState) -> ExecutionBlueprint:
        task_ids = tuple(task.identifier for task in blueprint.task_graph)
        milestone = PlannedMilestone(
            identifier="milestone_1",
            objective=blueprint.execution_objective.primary_objective if blueprint.execution_objective else (cognitive_state.normalized_goal or "Unknown objective"),
            tasks=task_ids,
            completion_conditions=("Blueprint approved", "All task groups identified"),
            expected_outputs=blueprint.expected_deliverables,
        )
        return blueprint.with_updates(milestones=(milestone,))


class PriorityPlanner:
    stage_name = "Priority Planning"

    def plan(self, blueprint: ExecutionBlueprint, cognitive_state: CognitiveState) -> ExecutionBlueprint:
        ordered = tuple(task.identifier for task in blueprint.task_graph)
        return blueprint.with_updates(priority_ordering=ordered)


class RiskAssessment:
    stage_name = "Risk Assessment"

    def plan(self, blueprint: ExecutionBlueprint, cognitive_state: CognitiveState) -> ExecutionBlueprint:
        risks: list[RiskAssessmentItem] = []
        text = cognitive_state.raw_request.lower()
        if "unknown" in (blueprint.execution_objective.primary_objective or "").lower():
            risks.append(RiskAssessmentItem("missing_information", "high", "medium", 0.8, "Primary objective is not fully known."))
        if any(token in text for token in ["database", "provider", "streaming", "frontend"]):
            risks.append(RiskAssessmentItem("external_dependency", "medium", "high", 0.7, "Request references external integration boundaries."))
        if cognitive_state.complexity_assessment and cognitive_state.complexity_assessment.reasoning_complexity == "high":
            risks.append(RiskAssessmentItem("high_complexity", "medium", "medium", 0.75, "Cognitive assessment indicates high reasoning complexity."))
        if not risks:
            risks.append(RiskAssessmentItem("unknown", "unknown", "unknown", 0.4, "No concrete risk could be inferred."))
        return blueprint.with_updates(estimated_risks=tuple(risks))


class BlueprintAssembler:
    stage_name = "Blueprint Assembly"

    def plan(self, blueprint: ExecutionBlueprint, cognitive_state: CognitiveState) -> ExecutionBlueprint:
        confidence = min(
            [
                *(intent.confidence for intent in cognitive_state.intent_collection),
                cognitive_state.complexity_assessment.confidence if cognitive_state.complexity_assessment else 0.5,
            ]
        ) if cognitive_state.intent_collection or cognitive_state.complexity_assessment else 0.5
        assumptions = ("Planning artifacts remain request-scoped.", "Execution remains delegated to Runtime V1.")
        return blueprint.with_updates(
            required_runtime_capabilities=cognitive_state.required_runtime_capabilities,
            execution_assumptions=assumptions,
            planning_confidence=round(confidence, 2),
        )


class PlanningEngine:
    def __init__(self, stages: list[PlanningStage] | None = None, planning_version: str = "1.0") -> None:
        self.stages = stages or [
            ObjectivePlanner(),
            TaskDecomposer(),
            DependencyBuilder(),
            MilestoneBuilder(),
            PriorityPlanner(),
            RiskAssessment(),
            BlueprintAssembler(),
        ]
        self.planning_version = planning_version

    def plan(self, *, cognitive_state: CognitiveState, runtime_version: str, request_id: str | None = None) -> ExecutionBlueprint:
        start = datetime.now(timezone.utc)
        metadata = PlanningMetadata(
            runtime_version=runtime_version,
            planning_version=self.planning_version,
            request_id=request_id or getattr(cognitive_state.processing_metadata, "request_id", str(uuid.uuid4())),
            trace_id=str(uuid.uuid4()),
            created_at=start.isoformat(),
            planning_duration=0.0,
        )
        blueprint = ExecutionBlueprint(
            planning_metadata=metadata,
            raw_cognitive_state=cognitive_state,
        )
        trace: list[PlanningTraceEntry] = []
        current = blueprint
        for stage in self.stages:
            stage_start = datetime.now(timezone.utc)
            before = current
            status = "COMPLETED"
            summary = "Completed."
            confidence = 0.5
            try:
                current = stage.plan(current, cognitive_state)
                summary = self._summarize_stage(stage.stage_name, current)
                confidence = current.planning_confidence or 0.5
            except Exception as exc:
                status = "FAILED"
                summary = str(exc)
                confidence = 0.0
                current = before
            stage_end = datetime.now(timezone.utc)
            trace.append(
                PlanningTraceEntry(
                    stage_name=stage.stage_name,
                    started_at=stage_start.isoformat(),
                    completed_at=stage_end.isoformat(),
                    duration=(stage_end - stage_start).total_seconds(),
                    status=status,
                    summary=summary,
                    confidence=confidence,
                    input_snapshot=self._safe_snapshot(before),
                    output_snapshot=self._safe_snapshot(current),
                )
            )
        end = datetime.now(timezone.utc)
        current = current.with_updates(
            planning_metadata=replace(metadata, planning_duration=(end - start).total_seconds()),
            planning_trace=tuple(trace),
        )
        return current

    def _summarize_stage(self, stage_name: str, blueprint: ExecutionBlueprint) -> str:
        if stage_name == "Objective Planning" and blueprint.execution_objective:
            return blueprint.execution_objective.primary_objective or "Unknown objective"
        if stage_name == "Task Decomposition":
            return f"{len(blueprint.task_graph)} tasks"
        if stage_name == "Dependency Graph":
            return f"{len(blueprint.dependency_graph)} dependencies"
        if stage_name == "Milestone Planning":
            return f"{len(blueprint.milestones)} milestones"
        if stage_name == "Priority Planning":
            return ", ".join(blueprint.priority_ordering)
        if stage_name == "Risk Assessment":
            return ", ".join(risk.risk_type for risk in blueprint.estimated_risks)
        if stage_name == "Blueprint Assembly":
            return f"confidence={blueprint.planning_confidence}"
        return "Completed."

    def _safe_snapshot(self, blueprint: ExecutionBlueprint) -> dict[str, Any]:
        return {
            "objective": blueprint.execution_objective.primary_objective if blueprint.execution_objective else None,
            "tasks": [task.__dict__ for task in blueprint.task_graph],
            "dependencies": [edge.__dict__ for edge in blueprint.dependency_graph],
            "milestones": [milestone.__dict__ for milestone in blueprint.milestones],
            "risks": [risk.__dict__ for risk in blueprint.estimated_risks],
        }


def _secondary_objectives_from_intents(intents: tuple[CognitiveIntent, ...]) -> list[str]:
    return [intent.category for intent in intents if intent.category not in {"explanation"}][:3]


def _deliverables_from_goal(goal: str) -> list[str]:
    return [f"Structured plan for {goal}", "Execution blueprint"]


def _completion_criteria_from_goal(goal: str, deliverables: tuple[str, ...]) -> list[str]:
    criteria = [f"Goal captured: {goal}"]
    criteria.extend(f"Deliverable ready: {deliverable}" for deliverable in deliverables)
    return criteria
