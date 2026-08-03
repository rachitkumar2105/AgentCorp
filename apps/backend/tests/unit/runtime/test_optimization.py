"""Unit tests for runtime optimization."""

from __future__ import annotations

import asyncio

from app.runtime.long_term_intelligence import LongTermIntelligenceReport
from app.runtime.optimization import OptimizationPolicy, RuntimeOptimizationEngine
from app.services.observability_service import ObservabilityService


def _long_term_report() -> LongTermIntelligenceReport:
    return LongTermIntelligenceReport(
        consolidated_memories=(),
        forgotten_memories=(),
        evolved_preferences=(),
        discovered_patterns=(),
        capability_scores={
            "Provider": {"success_rate": 0.91, "average_latency": 0.7, "confidence": 0.88, "historical_usage": 6.0, "failure_frequency": 0.09},
            "Workflow": {"success_rate": 0.83, "average_latency": 1.2, "confidence": 0.8, "historical_usage": 4.0, "failure_frequency": 0.17},
        },
        long_term_knowledge=(),
        intelligence_confidence=0.84,
        persisted=True,
        started_at="2026-08-02T00:00:00+00:00",
        completed_at="2026-08-02T00:00:00+00:00",
        duration=0.0,
        trace=(),
        metadata={"organization_id": 1, "agent_id": 1},
    )


def test_runtime_optimization_engine_is_deterministic() -> None:
    engine = RuntimeOptimizationEngine()
    report = engine.optimize(
        long_term_report=_long_term_report(),
        optimization_policy=OptimizationPolicy.QUALITY,
        workflow_history={
            "workflow_a": {"success_rate": 0.6, "average_duration": 5.0, "failure_rate": 0.1},
            "workflow_b": {"success_rate": 0.9, "average_duration": 3.0, "failure_rate": 0.05},
        },
        tool_history={"tool_a": {"success_rate": 0.7, "latency": 2.0, "reliability": 0.8, "usage_frequency": 3.0}},
        prompt_history={"concise": {"effectiveness": 0.9, "latency": 1.0, "cost": 0.5}},
    )

    assert report.policy == OptimizationPolicy.QUALITY
    assert report.provider_recommendation.recommendation == "Provider"
    assert report.workflow_recommendation.target == "workflow"
    assert report.tool_recommendation.target == "tool"
    assert report.prompt_recommendation.target == "prompt"
    assert report.capability_recommendation.target == "capability"
    assert report.trace[0]["stage_name"] == "Runtime Optimization Started"
    assert report.trace[-1]["stage_name"] == "Runtime Optimization Completed"
    assert report.estimated_improvement >= 0


def test_runtime_observatory_includes_runtime_optimization() -> None:
    service = ObservabilityService.__new__(ObservabilityService)
    snapshot = {
        "last_runtime_optimization": {"policy": "balanced", "estimated_improvement": 0.2},
        "active_runtime_optimizations": [{"policy": "balanced", "estimated_improvement": 0.2}],
    }

    async def fake_get_diagnostics():
        return snapshot

    async def fake_get_traces():
        return []

    service.get_diagnostics = fake_get_diagnostics  # type: ignore[method-assign]
    service.get_active_traces = fake_get_traces  # type: ignore[method-assign]

    observatory = asyncio.run(service.get_runtime_observatory())
    assert observatory["runtime_optimization"]["policy"] == "balanced"
    assert observatory["runtime_optimizations"][0]["estimated_improvement"] == 0.2
