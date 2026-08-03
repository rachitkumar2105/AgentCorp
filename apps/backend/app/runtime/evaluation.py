"""
Runtime V2 evaluation engine.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from app.runtime.execution import ExecutionContext, ExecutionResult
from app.runtime.reflection import ReflectionReport


@dataclass(frozen=True)
class EvaluationReportMetadata:
    runtime_version: str
    execution_id: str | None
    request_id: str | None
    trace_id: str | None
    created_at: str


@dataclass(frozen=True)
class EvaluationScore:
    name: str
    score: float
    summary: str


@dataclass(frozen=True)
class EvaluationReport:
    success: bool
    confidence: float
    completeness_score: float
    consistency_score: float
    efficiency_score: float
    quality_score: float
    capability_utilization: tuple[str, ...]
    evaluation_summary: str
    scores: tuple[EvaluationScore, ...]
    metadata: EvaluationReportMetadata
    started_at: str
    completed_at: str
    duration: float


class EvaluationEngine:
    def evaluate(
        self,
        *,
        execution_context: ExecutionContext,
        execution_result: ExecutionResult,
        reflection_report: ReflectionReport,
    ) -> EvaluationReport:
        started_at = datetime.now(timezone.utc)
        completeness_score = _completeness_score(execution_context, execution_result, reflection_report)
        consistency_score = _consistency_score(execution_result, reflection_report)
        efficiency_score = _efficiency_score(execution_result)
        quality_score = round((completeness_score + consistency_score + efficiency_score) / 3, 2)
        confidence = round(min(0.99, (reflection_report.confidence + quality_score) / 2), 2)
        success = execution_result.status.value == "COMPLETED" and quality_score >= 0.6
        capability_utilization = tuple(
            [str(execution_result.metadata.get("required_capability"))]
            if execution_result.metadata.get("required_capability")
            else []
        )
        scores = (
            EvaluationScore("completeness", completeness_score, "Presence of execution result, trace, and context signals."),
            EvaluationScore("consistency", consistency_score, "Alignment between reflection and execution status."),
            EvaluationScore("efficiency", efficiency_score, "Duration and error-free execution."),
            EvaluationScore("quality", quality_score, "Aggregated evaluation score."),
        )
        completed_at = datetime.now(timezone.utc)
        return EvaluationReport(
            success=success,
            confidence=confidence,
            completeness_score=completeness_score,
            consistency_score=consistency_score,
            efficiency_score=efficiency_score,
            quality_score=quality_score,
            capability_utilization=capability_utilization,
            evaluation_summary=_build_summary(success, quality_score, reflection_report),
            scores=scores,
            metadata=EvaluationReportMetadata(
                runtime_version=execution_context.runtime_version,
                execution_id=execution_context.execution_metadata.execution_id if execution_context.execution_metadata else None,
                request_id=execution_context.execution_metadata.request_id if execution_context.execution_metadata else None,
                trace_id=execution_context.execution_metadata.trace_id if execution_context.execution_metadata else None,
                created_at=started_at.isoformat(),
            ),
            started_at=started_at.isoformat(),
            completed_at=completed_at.isoformat(),
            duration=(completed_at - started_at).total_seconds(),
        )


def _completeness_score(execution_context: ExecutionContext, execution_result: ExecutionResult, reflection_report: ReflectionReport) -> float:
    score = 0.4
    if execution_context.execution_blueprint is not None:
        score += 0.2
    if execution_result.outputs:
        score += 0.2
    if reflection_report.observations:
        score += 0.2
    return round(min(score, 1.0), 2)


def _consistency_score(execution_result: ExecutionResult, reflection_report: ReflectionReport) -> float:
    score = 0.5
    if execution_result.status.value == "COMPLETED" and not reflection_report.weaknesses:
        score += 0.3
    if reflection_report.warnings:
        score -= 0.1
    return round(max(min(score, 1.0), 0.0), 2)


def _efficiency_score(execution_result: ExecutionResult) -> float:
    if execution_result.duration <= 0:
        return 0.2
    if execution_result.duration < 1:
        return 0.9
    if execution_result.duration < 5:
        return 0.75
    return 0.6


def _build_summary(success: bool, quality_score: float, reflection_report: ReflectionReport) -> str:
    verdict = "successful" if success else "needs review"
    return f"Evaluation {verdict} with quality {quality_score:.2f}. {reflection_report.execution_summary}"
