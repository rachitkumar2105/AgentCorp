"""
Runtime V2 learning and experience layer.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import Enum

from app.runtime.evaluation import EvaluationReport
from app.runtime.execution import ExecutionContext, RuntimeLifecycleEntry
from app.runtime.reflection import ReflectionReport


class LearningDecision(str, Enum):
    PERSIST = "persist"
    IGNORE = "ignore"
    MERGE = "merge"
    UPDATE = "update"
    DEFER = "defer"


@dataclass(frozen=True)
class LearningReportMetadata:
    runtime_version: str
    execution_id: str | None
    request_id: str | None
    trace_id: str | None
    created_at: str


@dataclass(frozen=True)
class LearningArtifact:
    category: str
    title: str
    summary: str
    confidence: float


@dataclass(frozen=True)
class LearningReport:
    reusable_observations: tuple[LearningArtifact, ...]
    reusable_preferences: tuple[LearningArtifact, ...]
    reusable_execution_patterns: tuple[LearningArtifact, ...]
    reusable_capability_patterns: tuple[LearningArtifact, ...]
    reusable_workflow_patterns: tuple[LearningArtifact, ...]
    confidence: float
    learning_priority: int
    persistence_recommendation: LearningDecision
    metadata: LearningReportMetadata
    started_at: str
    completed_at: str
    duration: float
    summary: str


@dataclass(frozen=True)
class LearningPolicyDecision:
    decision: LearningDecision
    reason: str
    persist_memory: bool
    memory_type: str | None = None
    importance_score: float = 0.0


class LearningPolicy:
    def decide(self, report: LearningReport) -> LearningPolicyDecision:
        if report.confidence < 0.45:
            return LearningPolicyDecision(LearningDecision.IGNORE, "Confidence too low for persistence.", False)
        if report.persistence_recommendation == LearningDecision.DEFER:
            return LearningPolicyDecision(LearningDecision.DEFER, "Analysis is useful but should be deferred.", False)
        if report.persistence_recommendation == LearningDecision.UPDATE:
            return LearningPolicyDecision(LearningDecision.UPDATE, "Existing experience should be updated.", True, "semantic", report.confidence)
        if report.persistence_recommendation == LearningDecision.MERGE:
            return LearningPolicyDecision(LearningDecision.MERGE, "Artifacts should be merged with existing experience.", True, "semantic", report.confidence)
        if report.persistence_recommendation == LearningDecision.PERSIST:
            return LearningPolicyDecision(LearningDecision.PERSIST, "Analysis is strong enough to persist.", True, "episodic", report.confidence)
        return LearningPolicyDecision(LearningDecision.IGNORE, "No reusable experience identified.", False)


class LearningEngine:
    def learn(
        self,
        *,
        execution_context: ExecutionContext,
        reflection_report: ReflectionReport,
        evaluation_report: EvaluationReport,
        execution_trace: tuple[RuntimeLifecycleEntry, ...],
    ) -> LearningReport:
        started_at = datetime.now(timezone.utc)
        reusable_observations = self._extract_observations(reflection_report)
        reusable_preferences = self._extract_preferences(execution_context, evaluation_report)
        reusable_execution_patterns = self._extract_execution_patterns(execution_context, reflection_report, evaluation_report, execution_trace)
        reusable_capability_patterns = self._extract_capability_patterns(execution_context, evaluation_report)
        reusable_workflow_patterns = self._extract_workflow_patterns(execution_context, execution_trace)
        confidence = self._score_confidence(reflection_report, evaluation_report, reusable_observations, reusable_preferences)
        persistence_recommendation = self._recommend_persistence(
            confidence=confidence,
            reusable_preferences=reusable_preferences,
            reusable_execution_patterns=reusable_execution_patterns,
            reusable_capability_patterns=reusable_capability_patterns,
            reusable_workflow_patterns=reusable_workflow_patterns,
        )
        completed_at = datetime.now(timezone.utc)
        return LearningReport(
            reusable_observations=tuple(reusable_observations),
            reusable_preferences=tuple(reusable_preferences),
            reusable_execution_patterns=tuple(reusable_execution_patterns),
            reusable_capability_patterns=tuple(reusable_capability_patterns),
            reusable_workflow_patterns=tuple(reusable_workflow_patterns),
            confidence=confidence,
            learning_priority=self._priority_from_scores(confidence, evaluation_report.quality_score),
            persistence_recommendation=persistence_recommendation,
            metadata=LearningReportMetadata(
                runtime_version=execution_context.runtime_version,
                execution_id=execution_context.execution_metadata.execution_id if execution_context.execution_metadata else None,
                request_id=execution_context.execution_metadata.request_id if execution_context.execution_metadata else None,
                trace_id=execution_context.execution_metadata.trace_id if execution_context.execution_metadata else None,
                created_at=started_at.isoformat(),
            ),
            started_at=started_at.isoformat(),
            completed_at=completed_at.isoformat(),
            duration=(completed_at - started_at).total_seconds(),
            summary=self._build_summary(reusable_observations, reusable_preferences, reusable_execution_patterns),
        )

    def _extract_observations(self, reflection_report: ReflectionReport) -> list[LearningArtifact]:
        observations = [
            LearningArtifact("observation", obs.category, obs.summary, reflection_report.confidence)
            for obs in reflection_report.observations
        ]
        observations.extend(
            LearningArtifact("observation", "strength", strength, reflection_report.confidence)
            for strength in reflection_report.strengths
        )
        return observations

    def _extract_preferences(self, execution_context: ExecutionContext, evaluation_report: EvaluationReport) -> list[LearningArtifact]:
        text = str(getattr(execution_context.original_request, "message", execution_context.original_request)).lower()
        preferences: list[LearningArtifact] = []
        if any(token in text for token in ("concise", "brief", "short")):
            preferences.append(LearningArtifact("preference", "communication", "Prefers concise responses.", evaluation_report.confidence))
        if any(token in text for token in ("bullet", "list", "structured")):
            preferences.append(LearningArtifact("preference", "formatting", "Prefers structured formatting.", evaluation_report.confidence))
        if any(token in text for token in ("english", "spanish", "french")):
            preferences.append(LearningArtifact("preference", "language", "Language preference detected from request.", evaluation_report.confidence))
        if "workflow" in text or "tool" in text:
            preferences.append(LearningArtifact("preference", "workflow", "Workflow-oriented request.", evaluation_report.confidence))
        return preferences

    def _extract_execution_patterns(
        self,
        execution_context: ExecutionContext,
        reflection_report: ReflectionReport,
        evaluation_report: EvaluationReport,
        execution_trace: tuple[RuntimeLifecycleEntry, ...],
    ) -> list[LearningArtifact]:
        patterns: list[LearningArtifact] = []
        if execution_trace:
            stage_names = " -> ".join(entry.stage_name for entry in execution_trace[-4:])
            patterns.append(
                LearningArtifact(
                    "execution_pattern",
                    "lifecycle_sequence",
                    stage_names,
                    min(reflection_report.confidence, evaluation_report.confidence),
                )
            )
        if evaluation_report.success:
            patterns.append(
                LearningArtifact(
                    "execution_pattern",
                    "successful_execution",
                    "Completed execution with a successful evaluation.",
                    evaluation_report.confidence,
                )
            )
        return patterns

    def _extract_capability_patterns(self, execution_context: ExecutionContext, evaluation_report: EvaluationReport) -> list[LearningArtifact]:
        patterns: list[LearningArtifact] = []
        for capability in evaluation_report.capability_utilization:
            patterns.append(
                LearningArtifact(
                    "capability_pattern",
                    capability,
                    f"Capability {capability} was used successfully.",
                    evaluation_report.confidence,
                )
            )
        if execution_context.execution_blueprint and len(execution_context.execution_blueprint.required_runtime_capabilities) > 1:
            patterns.append(
                LearningArtifact(
                    "capability_pattern",
                    "multi_capability_request",
                    "Request required more than one runtime capability.",
                    evaluation_report.confidence,
                )
            )
        return patterns

    def _extract_workflow_patterns(self, execution_context: ExecutionContext, execution_trace: tuple[RuntimeLifecycleEntry, ...]) -> list[LearningArtifact]:
        if not execution_context.execution_blueprint:
            return []
        stages = tuple(execution_context.execution_blueprint.execution_stages)
        return [
            LearningArtifact(
                "workflow_pattern",
                "planning_sequence",
                " -> ".join(stages) if stages else "No staged workflow was present.",
                0.5,
            ),
            LearningArtifact(
                "workflow_pattern",
                "trace_depth",
                f"{len(execution_trace)} trace entries captured.",
                0.5,
            ),
        ]

    def _recommend_persistence(
        self,
        *,
        confidence: float,
        reusable_preferences: list[LearningArtifact],
        reusable_execution_patterns: list[LearningArtifact],
        reusable_capability_patterns: list[LearningArtifact],
        reusable_workflow_patterns: list[LearningArtifact],
    ) -> LearningDecision:
        if confidence >= 0.85 and (reusable_preferences or reusable_execution_patterns):
            return LearningDecision.PERSIST
        if confidence >= 0.72 and reusable_capability_patterns:
            return LearningDecision.MERGE
        if confidence >= 0.6 and reusable_workflow_patterns:
            return LearningDecision.UPDATE
        if confidence >= 0.5:
            return LearningDecision.DEFER
        return LearningDecision.IGNORE

    def _priority_from_scores(self, confidence: float, quality_score: float) -> int:
        return 3 if confidence >= 0.85 or quality_score >= 0.85 else 2 if confidence >= 0.7 else 1

    def _score_confidence(
        self,
        reflection_report: ReflectionReport,
        evaluation_report: EvaluationReport,
        reusable_observations: list[LearningArtifact],
        reusable_preferences: list[LearningArtifact],
    ) -> float:
        score = (reflection_report.confidence + evaluation_report.confidence + evaluation_report.quality_score) / 3
        if reusable_observations:
            score += 0.05
        if reusable_preferences:
            score += 0.05
        return round(min(score, 0.99), 2)

    def _build_summary(
        self,
        reusable_observations: list[LearningArtifact],
        reusable_preferences: list[LearningArtifact],
        reusable_execution_patterns: list[LearningArtifact],
    ) -> str:
        return (
            f"Learned {len(reusable_observations)} observations, "
            f"{len(reusable_preferences)} preferences, "
            f"and {len(reusable_execution_patterns)} execution patterns."
        )
