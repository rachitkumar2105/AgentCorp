"""Unit tests for long-term intelligence."""

from __future__ import annotations

import pytest

from app.runtime.adaptive_planning import AdaptivePlanningEngine
from app.runtime.cognitive import CognitiveEngine
from app.runtime.evaluation import EvaluationEngine
from app.runtime.goal_management import GoalEngine
from app.runtime.learning import LearningEngine
from app.runtime.long_term_intelligence import (
    CapabilityScoringEngine,
    ForgettingPolicy,
    LongTermIntelligenceEngine,
    MemoryConsolidationEngine,
    PatternDiscoveryEngine,
    PreferenceEvolutionEngine,
)
from app.runtime.planning import PlanningEngine
from app.runtime.reflection import ReflectionEngine
from app.runtime.execution import create_execution_context
from app.runtime.router import RuntimeVersion
from app.services.observability_service import ObservabilityService


def _build_reports(message: str):
    cognitive_state = CognitiveEngine().analyze(
        request_text=message,
        runtime_version=RuntimeVersion.V2.value,
        request_id="lti-req",
    )
    blueprint = PlanningEngine().plan(
        cognitive_state=cognitive_state,
        runtime_version=RuntimeVersion.V2.value,
        request_id="lti-req",
    )
    context = create_execution_context(
        original_request={"message": message},
        runtime_version=RuntimeVersion.V2.value,
        request_id="lti-req",
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
    adaptive_report = AdaptivePlanningEngine(PlanningEngine()).revise_blueprint(
        goal=GoalEngine().create_goal(
            title="Adaptive goal",
            objective=message,
            owner_id=1,
            organization_id=1,
        ),
        previous_blueprint=blueprint,
        reflection_report=reflection_report,
        evaluation_report=evaluation_report,
        learning_report=learning_report,
    )
    return learning_report, adaptive_report


class _DummyMemoryService:
    def __init__(self, memories):
        self.memories = memories
        self.created = []

    def list_memories(self, org_id, agent_id, memory_type=None):
        return self.memories

    def create_memory(self, **kwargs):
        self.created.append(kwargs)
        return kwargs


@pytest.mark.anyio
async def test_long_term_intelligence_engine_consolidates_and_persists():
    learning_report, adaptive_report = _build_reports("Provide a concise, structured workflow plan.")
    memories = [
        {
            "title": "User preference",
            "content": "Prefer concise responses.",
            "importance_score": 0.6,
            "confidence_score": 0.7,
            "memory_type": "semantic",
            "created_at": None,
            "updated_at": None,
            "source": "extraction",
        },
        {
            "title": "User preference",
            "content": "Prefer concise responses.",
            "importance_score": 0.8,
            "confidence_score": 0.9,
            "memory_type": "semantic",
            "created_at": None,
            "updated_at": None,
            "source": "manual",
        },
        {
            "title": "Stale note",
            "content": "Old item.",
            "importance_score": 0.1,
            "confidence_score": 0.1,
            "memory_type": "semantic",
            "created_at": None,
            "updated_at": None,
            "source": "extraction",
        },
    ]
    service = _DummyMemoryService(memories)
    engine = LongTermIntelligenceEngine(memory_service=service)

    report = await engine.persist_intelligence(
        organization_id=1,
        agent_id=7,
        current_user=type("User", (), {"id": 99})(),
        learning_report=learning_report,
        adaptive_report=adaptive_report,
    )

    assert report.persisted is True
    assert report.consolidated_memories
    assert report.evolved_preferences
    assert report.discovered_patterns
    assert report.capability_scores["Memory"]["success_rate"] >= 0.35
    assert service.created
    assert report.trace[0]["stage_name"] == "Long-Term Intelligence Started"
    assert report.trace[-1]["stage_name"] == "Long-Term Intelligence Completed"


def test_forgetting_policy_is_deterministic():
    policy = ForgettingPolicy()
    memory = {"confidence_score": 0.1, "created_at": None}
    assert policy.should_forget(memory) is True
    assert policy.should_forget(memory) is True


def test_memory_consolidation_merges_duplicates():
    consolidated, forgotten = MemoryConsolidationEngine().consolidate(
        [
            {"title": "duplicate", "confidence_score": 0.4, "importance_score": 0.3, "source": "a"},
            {"title": "duplicate", "confidence_score": 0.9, "importance_score": 0.8, "source": "b"},
        ]
    )
    assert len(consolidated) == 1
    assert consolidated[0]["confidence_score"] == 0.9
    assert forgotten == []


def test_runtime_observatory_includes_long_term_intelligence():
    service = ObservabilityService.__new__(ObservabilityService)
    snapshot = {
        "last_long_term_intelligence": {"intelligence_confidence": 0.8},
        "active_long_term_intelligence": [{"intelligence_confidence": 0.8}],
    }

    async def fake_get_diagnostics():
        return snapshot

    async def fake_get_traces():
        return []

    service.get_diagnostics = fake_get_diagnostics  # type: ignore[method-assign]
    service.get_active_traces = fake_get_traces  # type: ignore[method-assign]

    import asyncio

    observatory = asyncio.run(service.get_runtime_observatory())
    assert observatory["long_term_intelligence"]["intelligence_confidence"] == 0.8
    assert observatory["long_term_intelligences"][0]["intelligence_confidence"] == 0.8
