"""
Runtime V2 reflection engine.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import Any

from app.runtime.execution import ExecutionContext, ExecutionResult, RuntimeLifecycleEntry


@dataclass(frozen=True)
class ReflectionReportMetadata:
    runtime_version: str
    execution_id: str | None
    request_id: str | None
    trace_id: str | None
    created_at: str


@dataclass(frozen=True)
class ReflectionObservation:
    category: str
    summary: str
    detail: str | None = None


@dataclass(frozen=True)
class ReflectionReport:
    execution_summary: str
    observations: tuple[ReflectionObservation, ...]
    strengths: tuple[str, ...]
    weaknesses: tuple[str, ...]
    missing_information: tuple[str, ...]
    improvement_opportunities: tuple[str, ...]
    warnings: tuple[str, ...]
    metadata: ReflectionReportMetadata
    started_at: str
    completed_at: str
    duration: float
    confidence: float


class ReflectionEngine:
    def reflect(
        self,
        *,
        execution_context: ExecutionContext,
        execution_result: ExecutionResult,
        execution_trace: tuple[RuntimeLifecycleEntry, ...],
    ) -> ReflectionReport:
        started_at = datetime.now(timezone.utc)
        observations: list[ReflectionObservation] = []
        strengths: list[str] = []
        weaknesses: list[str] = []
        missing_information: list[str] = []
        improvement_opportunities: list[str] = []
        warnings: list[str] = []

        if execution_result.status.value == "COMPLETED":
            strengths.append("Execution completed successfully.")
        else:
            weaknesses.append(f"Execution finished with status {execution_result.status.value}.")

        if execution_result.errors:
            weaknesses.extend(execution_result.errors)
            warnings.extend(execution_result.errors)

        if execution_result.duration <= 0:
            improvement_opportunities.append("Capture more precise execution timing.")
            warnings.append("Execution duration was non-positive.")

        capability_name = execution_result.metadata.get("required_capability")
        if capability_name:
            observations.append(
                ReflectionObservation(
                    category="capability_usage",
                    summary=f"Used capability {capability_name}.",
                )
            )
        else:
            missing_information.append("Required capability metadata was absent.")

        if execution_trace:
            observations.append(
                ReflectionObservation(
                    category="trace",
                    summary=f"Observed {len(execution_trace)} lifecycle entries.",
                    detail=execution_trace[-1].stage_name,
                )
            )
        else:
            missing_information.append("No execution trace entries were provided.")

        if execution_context.execution_blueprint is None:
            missing_information.append("Execution blueprint was not attached to the context.")
        else:
            required_caps = execution_context.execution_blueprint.required_runtime_capabilities
            if len(required_caps) > 1:
                improvement_opportunities.append("Separate capability work from final-response capability selection.")

        confidence = _score_confidence(execution_result, execution_trace)
        completed_at = datetime.now(timezone.utc)
        return ReflectionReport(
            execution_summary=_build_summary(execution_result, execution_trace),
            observations=tuple(observations),
            strengths=tuple(strengths),
            weaknesses=tuple(weaknesses),
            missing_information=tuple(missing_information),
            improvement_opportunities=tuple(dict.fromkeys(improvement_opportunities)),
            warnings=tuple(dict.fromkeys(warnings)),
            metadata=ReflectionReportMetadata(
                runtime_version=execution_context.runtime_version,
                execution_id=execution_context.execution_metadata.execution_id if execution_context.execution_metadata else None,
                request_id=execution_context.execution_metadata.request_id if execution_context.execution_metadata else None,
                trace_id=execution_context.execution_metadata.trace_id if execution_context.execution_metadata else None,
                created_at=started_at.isoformat(),
            ),
            started_at=started_at.isoformat(),
            completed_at=completed_at.isoformat(),
            duration=(completed_at - started_at).total_seconds(),
            confidence=confidence,
        )


def _build_summary(execution_result: ExecutionResult, execution_trace: tuple[RuntimeLifecycleEntry, ...]) -> str:
    trace_summary = execution_trace[-1].summary if execution_trace else "No execution trace was available."
    return f"{execution_result.task_id} finished with {execution_result.status.value}. {trace_summary}"


def _score_confidence(execution_result: ExecutionResult, execution_trace: tuple[RuntimeLifecycleEntry, ...]) -> float:
    score = 0.5
    if execution_result.status.value == "COMPLETED":
        score += 0.2
    if not execution_result.errors:
        score += 0.1
    if execution_trace:
        score += 0.1
    if execution_result.duration > 0:
        score += 0.1
    return round(min(score, 0.99), 2)
