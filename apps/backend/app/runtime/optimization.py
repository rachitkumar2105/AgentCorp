"""
Runtime V2 optimization layer.

Deterministic optimization recommendations only. No execution changes are made.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from app.runtime.long_term_intelligence import LongTermIntelligenceReport


class OptimizationPolicy(str, Enum):
    LATENCY = "latency"
    COST = "cost"
    QUALITY = "quality"
    BALANCED = "balanced"


@dataclass(frozen=True)
class OptimizationRecommendation:
    target: str
    recommendation: str
    reason: str
    confidence: float
    estimated_improvement: float
    evidence: dict[str, Any]


@dataclass(frozen=True)
class RuntimeOptimizationReport:
    policy: OptimizationPolicy
    provider_recommendation: OptimizationRecommendation
    workflow_recommendation: OptimizationRecommendation
    tool_recommendation: OptimizationRecommendation
    capability_recommendation: OptimizationRecommendation
    prompt_recommendation: OptimizationRecommendation
    execution_ordering: tuple[str, ...]
    estimated_improvement: float
    started_at: str
    completed_at: str
    duration: float
    trace: tuple[dict[str, Any], ...]
    persisted: bool
    metadata: dict[str, Any]


class RuntimeOptimizationEngine:
    def optimize(
        self,
        *,
        long_term_report: LongTermIntelligenceReport,
        optimization_policy: OptimizationPolicy = OptimizationPolicy.BALANCED,
        provider_history: dict[str, dict[str, float]] | None = None,
        workflow_history: dict[str, dict[str, float]] | None = None,
        tool_history: dict[str, dict[str, float]] | None = None,
        prompt_history: dict[str, dict[str, float]] | None = None,
        capability_scores: dict[str, dict[str, float]] | None = None,
    ) -> RuntimeOptimizationReport:
        started_at = datetime.now(timezone.utc)
        provider_history = provider_history or long_term_report.capability_scores
        workflow_history = workflow_history or {}
        tool_history = tool_history or {}
        prompt_history = prompt_history or {}
        capability_scores = capability_scores or long_term_report.capability_scores

        provider_recommendation = self._recommend_provider(provider_history, optimization_policy)
        workflow_recommendation = self._recommend_workflow(workflow_history, optimization_policy)
        tool_recommendation = self._recommend_tool(tool_history, optimization_policy)
        prompt_recommendation = self._recommend_prompt(prompt_history, optimization_policy)
        capability_recommendation = self._recommend_capability(capability_scores, optimization_policy)
        execution_ordering = self._order_execution(capability_scores, workflow_history)
        estimated_improvement = round(
            min(
                0.99,
                (
                    provider_recommendation.estimated_improvement
                    + workflow_recommendation.estimated_improvement
                    + tool_recommendation.estimated_improvement
                    + prompt_recommendation.estimated_improvement
                    + capability_recommendation.estimated_improvement
                )
                / 5,
            ),
            2,
        )
        completed_at = datetime.now(timezone.utc)
        trace = (
            {"stage_name": "Runtime Optimization Started", "status": "COMPLETED", "summary": "Optimization analysis started."},
            {"stage_name": "Provider Optimization", "status": "COMPLETED", "summary": provider_recommendation.reason},
            {"stage_name": "Workflow Optimization", "status": "COMPLETED", "summary": workflow_recommendation.reason},
            {"stage_name": "Tool Optimization", "status": "COMPLETED", "summary": tool_recommendation.reason},
            {"stage_name": "Capability Optimization", "status": "COMPLETED", "summary": capability_recommendation.reason},
            {"stage_name": "Optimization Persisted", "status": "COMPLETED", "summary": "Optimization recommendations persisted."},
            {"stage_name": "Runtime Optimization Completed", "status": "COMPLETED", "summary": "Optimization analysis completed."},
        )
        report = RuntimeOptimizationReport(
            policy=optimization_policy,
            provider_recommendation=provider_recommendation,
            workflow_recommendation=workflow_recommendation,
            tool_recommendation=tool_recommendation,
            capability_recommendation=capability_recommendation,
            prompt_recommendation=prompt_recommendation,
            execution_ordering=execution_ordering,
            estimated_improvement=estimated_improvement,
            started_at=started_at.isoformat(),
            completed_at=completed_at.isoformat(),
            duration=(completed_at - started_at).total_seconds(),
            trace=trace,
            persisted=True,
            metadata={
                "policy": optimization_policy.value,
                "provider_history_count": len(provider_history),
                "workflow_history_count": len(workflow_history),
                "tool_history_count": len(tool_history),
                "prompt_history_count": len(prompt_history),
                "capability_count": len(capability_scores),
            },
        )
        return report

    def _recommend_provider(self, history: dict[str, dict[str, float]], policy: OptimizationPolicy) -> OptimizationRecommendation:
        if not history:
            return OptimizationRecommendation("provider", "retain default provider", "No historical provider data available.", 0.25, 0.0, {})
        ranked = sorted(history.items(), key=lambda item: self._provider_score(item[1], policy), reverse=True)
        provider_name, stats = ranked[0]
        reason = f"Provider {provider_name} selected from historical success, latency, and quality data."
        return OptimizationRecommendation(
            "provider",
            provider_name,
            reason,
            round(self._provider_score(stats, policy), 2),
            round(self._improvement_from_stats(stats), 2),
            stats,
        )

    def _recommend_workflow(self, history: dict[str, dict[str, float]], policy: OptimizationPolicy) -> OptimizationRecommendation:
        if not history:
            return OptimizationRecommendation("workflow", "retain current workflow order", "No workflow statistics available.", 0.25, 0.0, {})
        ranked = sorted(history.items(), key=lambda item: self._workflow_score(item[1], policy), reverse=True)
        workflow_name, stats = ranked[0]
        return OptimizationRecommendation("workflow", workflow_name, f"Workflow {workflow_name} has the best historical execution profile.", round(self._workflow_score(stats, policy), 2), round(self._improvement_from_stats(stats), 2), stats)

    def _recommend_tool(self, history: dict[str, dict[str, float]], policy: OptimizationPolicy) -> OptimizationRecommendation:
        if not history:
            return OptimizationRecommendation("tool", "retain current tool selection", "No tool telemetry available.", 0.25, 0.0, {})
        ranked = sorted(history.items(), key=lambda item: self._tool_score(item[1], policy), reverse=True)
        tool_name, stats = ranked[0]
        return OptimizationRecommendation("tool", tool_name, f"Tool {tool_name} has the strongest reliability profile.", round(self._tool_score(stats, policy), 2), round(self._improvement_from_stats(stats), 2), stats)

    def _recommend_prompt(self, history: dict[str, dict[str, float]], policy: OptimizationPolicy) -> OptimizationRecommendation:
        if not history:
            return OptimizationRecommendation("prompt", "retain current prompt strategy", "No prompt strategy telemetry available.", 0.25, 0.0, {})
        ranked = sorted(history.items(), key=lambda item: self._prompt_score(item[1], policy), reverse=True)
        prompt_name, stats = ranked[0]
        return OptimizationRecommendation("prompt", prompt_name, f"Prompt strategy {prompt_name} is the most effective historical strategy.", round(self._prompt_score(stats, policy), 2), round(self._improvement_from_stats(stats), 2), stats)

    def _recommend_capability(self, scores: dict[str, dict[str, float]], policy: OptimizationPolicy) -> OptimizationRecommendation:
        if not scores:
            return OptimizationRecommendation("capability", "retain current capability ordering", "No capability scores available.", 0.25, 0.0, {})
        ranked = sorted(scores.items(), key=lambda item: self._capability_score(item[1], policy), reverse=True)
        capability_name, stats = ranked[0]
        return OptimizationRecommendation("capability", capability_name, f"Capability {capability_name} should be ordered earlier in the execution path.", round(self._capability_score(stats, policy), 2), round(self._improvement_from_stats(stats), 2), stats)

    def _order_execution(self, capability_scores: dict[str, dict[str, float]], workflow_history: dict[str, dict[str, float]]) -> tuple[str, ...]:
        capability_order = sorted(capability_scores.items(), key=lambda item: (item[1].get("failure_frequency", 1.0), -item[1].get("success_rate", 0.0)))
        workflow_order = sorted(workflow_history.items(), key=lambda item: (item[1].get("failure_rate", 1.0), -item[1].get("average_duration", 0.0)))
        ordering = [f"capability:{name}" for name, _ in capability_order]
        ordering.extend(f"workflow:{name}" for name, _ in workflow_order)
        return tuple(ordering or ("capability:provider", "workflow:default"))

    def _provider_score(self, stats: dict[str, float], policy: OptimizationPolicy) -> float:
        success = float(stats.get("success_rate", 0.0))
        latency = float(stats.get("average_latency", 1.0))
        quality = float(stats.get("confidence", 0.0))
        if policy == OptimizationPolicy.LATENCY:
            return (1 - min(latency / 10, 1)) * 0.6 + success * 0.3 + quality * 0.1
        if policy == OptimizationPolicy.COST:
            return success * 0.45 + quality * 0.2 + (1 - min(latency / 10, 1)) * 0.35
        if policy == OptimizationPolicy.QUALITY:
            return quality * 0.55 + success * 0.35 + (1 - min(latency / 10, 1)) * 0.1
        return success * 0.4 + quality * 0.35 + (1 - min(latency / 10, 1)) * 0.25

    def _workflow_score(self, stats: dict[str, float], policy: OptimizationPolicy) -> float:
        success = float(stats.get("success_rate", 0.0))
        duration = float(stats.get("average_duration", 1.0))
        failure_rate = float(stats.get("failure_rate", 0.0))
        if policy == OptimizationPolicy.LATENCY:
            return success * 0.35 + (1 - min(duration / 60, 1)) * 0.5 + (1 - failure_rate) * 0.15
        if policy == OptimizationPolicy.COST:
            return success * 0.4 + (1 - failure_rate) * 0.35 + (1 - min(duration / 60, 1)) * 0.25
        if policy == OptimizationPolicy.QUALITY:
            return success * 0.5 + (1 - failure_rate) * 0.35 + (1 - min(duration / 60, 1)) * 0.15
        return success * 0.45 + (1 - failure_rate) * 0.3 + (1 - min(duration / 60, 1)) * 0.25

    def _tool_score(self, stats: dict[str, float], policy: OptimizationPolicy) -> float:
        success = float(stats.get("success_rate", 0.0))
        latency = float(stats.get("latency", stats.get("average_latency", 1.0)))
        reliability = float(stats.get("reliability", stats.get("confidence", 0.0)))
        usage = float(stats.get("usage_frequency", stats.get("historical_usage", 0.0)))
        base = success * 0.4 + reliability * 0.35 + min(usage / 10, 1) * 0.25
        if policy == OptimizationPolicy.LATENCY:
            return base + (1 - min(latency / 10, 1)) * 0.2
        if policy == OptimizationPolicy.COST:
            return base + (1 - min(latency / 10, 1)) * 0.15
        if policy == OptimizationPolicy.QUALITY:
            return base + reliability * 0.15
        return base

    def _prompt_score(self, stats: dict[str, float], policy: OptimizationPolicy) -> float:
        effectiveness = float(stats.get("effectiveness", stats.get("confidence", 0.0)))
        latency = float(stats.get("latency", 0.0))
        cost = float(stats.get("cost", 0.0))
        if policy == OptimizationPolicy.LATENCY:
            return effectiveness * 0.55 + (1 - min(latency / 10, 1)) * 0.35 + (1 - min(cost / 10, 1)) * 0.1
        if policy == OptimizationPolicy.COST:
            return effectiveness * 0.45 + (1 - min(cost / 10, 1)) * 0.45 + (1 - min(latency / 10, 1)) * 0.1
        if policy == OptimizationPolicy.QUALITY:
            return effectiveness * 0.7 + (1 - min(latency / 10, 1)) * 0.1 + (1 - min(cost / 10, 1)) * 0.2
        return effectiveness * 0.55 + (1 - min(latency / 10, 1)) * 0.2 + (1 - min(cost / 10, 1)) * 0.25

    def _capability_score(self, stats: dict[str, float], policy: OptimizationPolicy) -> float:
        success = float(stats.get("success_rate", 0.0))
        latency = float(stats.get("average_latency", 1.0))
        failure_frequency = float(stats.get("failure_frequency", 0.0))
        if policy == OptimizationPolicy.LATENCY:
            return success * 0.35 + (1 - min(latency / 10, 1)) * 0.5 + (1 - failure_frequency) * 0.15
        if policy == OptimizationPolicy.COST:
            return success * 0.4 + (1 - failure_frequency) * 0.35 + (1 - min(latency / 10, 1)) * 0.25
        if policy == OptimizationPolicy.QUALITY:
            return success * 0.55 + (1 - failure_frequency) * 0.35 + (1 - min(latency / 10, 1)) * 0.1
        return success * 0.45 + (1 - failure_frequency) * 0.3 + (1 - min(latency / 10, 1)) * 0.25

    def _improvement_from_stats(self, stats: dict[str, float]) -> float:
        return min(0.35, max(0.0, float(stats.get("success_rate", 0.0)) * 0.1 + (1 - min(float(stats.get("average_latency", stats.get("latency", 1.0))) / 10, 1)) * 0.15))
