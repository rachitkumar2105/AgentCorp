"""
Cognitive understanding layer for Runtime V2.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import Any, Protocol
import re
import uuid


@dataclass(frozen=True)
class CognitiveProcessingMetadata:
    runtime_version: str
    analysis_version: str
    request_id: str
    trace_id: str
    created_at: str
    analysis_duration: float = 0.0


@dataclass(frozen=True)
class CognitiveIntent:
    category: str
    confidence: float
    evidence: str | None = None


@dataclass(frozen=True)
class CognitiveComplexityAssessment:
    reasoning_complexity: str
    execution_complexity: str
    dependency_complexity: str
    external_dependency_likelihood: str
    planning_depth: str
    confidence: float


@dataclass(frozen=True)
class CognitiveTraceEntry:
    stage_name: str
    started_at: str
    completed_at: str
    duration: float
    summary: str
    confidence: float
    warnings: list[str]
    errors: list[str]
    status: str
    input_snapshot: dict[str, Any] | None = None
    output_snapshot: dict[str, Any] | None = None


@dataclass(frozen=True)
class CognitiveState:
    normalized_goal: str | None = None
    intent_collection: tuple[CognitiveIntent, ...] = ()
    constraint_collection: tuple[str, ...] = ()
    context_requirements: tuple[str, ...] = ()
    required_runtime_capabilities: tuple[str, ...] = ()
    complexity_assessment: CognitiveComplexityAssessment | None = None
    confidence_assessments: dict[str, float] = None  # type: ignore[assignment]
    processing_metadata: CognitiveProcessingMetadata | None = None
    analysis_trace: tuple[CognitiveTraceEntry, ...] = ()
    raw_request: str = ""

    def with_updates(self, **kwargs: Any) -> "CognitiveState":
        return replace(self, **kwargs)


class CognitiveAnalyzer(Protocol):
    stage_name: str

    def analyze(self, state: CognitiveState) -> CognitiveState:
        ...


class GoalUnderstandingAnalyzer:
    stage_name = "Goal Understanding"

    def analyze(self, state: CognitiveState) -> CognitiveState:
        text = _normalize_text(state.raw_request)
        objective = _extract_primary_objective(text)
        summary = objective or text[:120]
        state = state.with_updates(
            normalized_goal=summary,
            confidence_assessments={**(state.confidence_assessments or {}), "goal": _confidence_from_text(text)},
        )
        return state


class IntentAnalyzer:
    stage_name = "Intent Analysis"

    def analyze(self, state: CognitiveState) -> CognitiveState:
        text = _normalize_text(state.raw_request)
        intents = []
        keywords = {
            "research": ["research", "find", "look up", "investigate"],
            "coding": ["code", "implement", "fix", "build", "write"],
            "writing": ["write", "draft", "compose", "summarize"],
            "planning": ["plan", "strategy", "roadmap"],
            "workflow": ["workflow", "pipeline", "process"],
            "tool usage": ["tool", "tooling", "execute"],
            "automation": ["automate", "automation", "scheduler"],
            "explanation": ["explain", "how does", "what is"],
            "summarization": ["summarize", "summary", "brief"],
        }
        for category, needles in keywords.items():
            evidence = next((needle for needle in needles if needle in text), None)
            if evidence:
                intents.append(CognitiveIntent(category=category, confidence=0.65, evidence=evidence))
        if not intents:
            intents.append(CognitiveIntent(category="explanation", confidence=0.35, evidence=None))
        return state.with_updates(
            intent_collection=tuple(intents),
            confidence_assessments={**(state.confidence_assessments or {}), "intent": max(i.confidence for i in intents)},
        )


class ConstraintAnalyzer:
    stage_name = "Constraint Analysis"

    def analyze(self, state: CognitiveState) -> CognitiveState:
        text = _normalize_text(state.raw_request)
        constraints = []
        for token in ["python", "fastapi", "sqlite", "postgres", "security", "organization", "compliance", "streaming", "frontend"]:
            if token in text:
                constraints.append(token)
        if "without changing" in text or "do not" in text:
            constraints.append("explicit_restrictions")
        if not constraints:
            constraints.append("unknown")
        return state.with_updates(
            constraint_collection=tuple(constraints),
            confidence_assessments={**(state.confidence_assessments or {}), "constraints": 0.6 if constraints else 0.2},
        )


class CapabilityAnalyzer:
    stage_name = "Capability Analysis"

    def analyze(self, state: CognitiveState) -> CognitiveState:
        text = _normalize_text(state.raw_request)
        caps = []
        mapping = [
            ("Memory", ["memory"]),
            ("Knowledge", ["knowledge"]),
            ("RAG", ["rag", "retrieval"]),
            ("Workflow", ["workflow"]),
            ("Tool Runtime", ["tool"]),
            ("Multi-Agent", ["multi-agent", "collaborative"]),
            ("Provider", ["provider", "model"]),
            ("Streaming", ["stream", "sse"]),
        ]
        for label, needles in mapping:
            if any(needle in text for needle in needles):
                caps.append(label)
        if not caps:
            caps.append("Provider")
        return state.with_updates(
            required_runtime_capabilities=tuple(caps),
            confidence_assessments={**(state.confidence_assessments or {}), "capabilities": 0.7},
        )


class ComplexityAnalyzer:
    stage_name = "Complexity Analysis"

    def analyze(self, state: CognitiveState) -> CognitiveState:
        text = _normalize_text(state.raw_request)
        word_count = len(text.split())
        reasoning = "high" if "architecture" in text or "integration" in text else "medium" if word_count > 20 else "low"
        execution = "high" if any(k in text for k in ["backend", "frontend", "runtime", "observatory"]) else "medium"
        dependency = "high" if any(k in text for k in ["database", "provider", "streaming", "multi-agent"]) else "low"
        external = "high" if any(k in text for k in ["frontend", "database", "provider"]) else "medium"
        planning = "high" if "phase" in text or "architecture" in text else "medium"
        assessment = CognitiveComplexityAssessment(
            reasoning_complexity=reasoning,
            execution_complexity=execution,
            dependency_complexity=dependency,
            external_dependency_likelihood=external,
            planning_depth=planning,
            confidence=0.66,
        )
        return state.with_updates(
            complexity_assessment=assessment,
            confidence_assessments={**(state.confidence_assessments or {}), "complexity": assessment.confidence},
        )


class CognitiveEngine:
    def __init__(self, analyzers: list[CognitiveAnalyzer] | None = None, analysis_version: str = "1.0") -> None:
        self.analyzers = analyzers or [
            GoalUnderstandingAnalyzer(),
            IntentAnalyzer(),
            ConstraintAnalyzer(),
            CapabilityAnalyzer(),
            ComplexityAnalyzer(),
        ]
        self.analysis_version = analysis_version

    def analyze(self, *, request_text: str, runtime_version: str, request_id: str | None = None) -> CognitiveState:
        start = datetime.now(timezone.utc)
        state = CognitiveState(
            raw_request=request_text,
            confidence_assessments={},
            processing_metadata=CognitiveProcessingMetadata(
                runtime_version=runtime_version,
                analysis_version=self.analysis_version,
                request_id=request_id or str(uuid.uuid4()),
                trace_id=str(uuid.uuid4()),
                created_at=start.isoformat(),
                analysis_duration=0.0,
            ),
        )
        trace = []
        for analyzer in self.analyzers:
            stage_start = datetime.now(timezone.utc)
            before = state
            errors: list[str] = []
            warnings: list[str] = []
            status = "COMPLETED"
            try:
                state = analyzer.analyze(state)
                summary = self._summarize_state(analyzer.stage_name, state)
                confidence = state.confidence_assessments.get(
                    analyzer.stage_name.lower().split()[0],
                    0.5,
                ) if state.confidence_assessments else 0.5
            except Exception as exc:
                status = "FAILED"
                summary = str(exc)
                confidence = 0.0
                errors.append(str(exc))
                state = before
            stage_end = datetime.now(timezone.utc)
            trace.append(
                CognitiveTraceEntry(
                    stage_name=analyzer.stage_name,
                    started_at=stage_start.isoformat(),
                    completed_at=stage_end.isoformat(),
                    duration=(stage_end - stage_start).total_seconds(),
                    summary=summary,
                    confidence=confidence,
                    warnings=warnings,
                    errors=errors,
                    status=status,
                    input_snapshot=self._safe_snapshot(before),
                    output_snapshot=self._safe_snapshot(state),
                )
            )
        end = datetime.now(timezone.utc)
        metadata = state.processing_metadata
        if metadata:
            metadata = replace(metadata, analysis_duration=(end - start).total_seconds())
            state = state.with_updates(processing_metadata=metadata)
        return state.with_updates(analysis_trace=tuple(trace))

    def _summarize_state(self, stage_name: str, state: CognitiveState) -> str:
        if stage_name == "Goal Understanding":
            return state.normalized_goal or "No goal identified."
        if stage_name == "Intent Analysis":
            return ", ".join(intent.category for intent in state.intent_collection)
        if stage_name == "Constraint Analysis":
            return ", ".join(state.constraint_collection)
        if stage_name == "Capability Analysis":
            return ", ".join(state.required_runtime_capabilities)
        if stage_name == "Complexity Analysis":
            assessment = state.complexity_assessment
            return f"{assessment.reasoning_complexity}/{assessment.execution_complexity}" if assessment else "No assessment."
        return "Completed."

    def _safe_snapshot(self, state: CognitiveState) -> dict[str, Any]:
        return {
            "normalized_goal": state.normalized_goal,
            "intents": [intent.__dict__ for intent in state.intent_collection],
            "constraints": list(state.constraint_collection),
            "capabilities": list(state.required_runtime_capabilities),
            "complexity": state.complexity_assessment.__dict__ if state.complexity_assessment else None,
        }


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _extract_primary_objective(text: str) -> str | None:
    if not text:
        return None
    for prefix in ["my request is", "i need", "please", "build", "create", "implement"]:
        if prefix in text:
            return text
    return text


def _confidence_from_text(text: str) -> float:
    if len(text.split()) > 40:
        return 0.8
    if len(text.split()) > 10:
        return 0.65
    return 0.4
