"""
Runtime V2 long-term intelligence layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from app.observability.diagnostics import register_long_term_intelligence
from app.runtime.adaptive_planning import AdaptivePlanningReport
from app.runtime.learning import LearningReport


@dataclass(frozen=True)
class LongTermKnowledge:
    title: str
    summary: str
    confidence: float
    knowledge_type: str
    provenance: dict[str, Any]


@dataclass(frozen=True)
class LongTermIntelligenceReport:
    consolidated_memories: tuple[dict[str, Any], ...]
    forgotten_memories: tuple[dict[str, Any], ...]
    evolved_preferences: tuple[dict[str, Any], ...]
    discovered_patterns: tuple[dict[str, Any], ...]
    capability_scores: dict[str, dict[str, float]]
    long_term_knowledge: tuple[LongTermKnowledge, ...]
    intelligence_confidence: float
    persisted: bool
    started_at: str
    completed_at: str
    duration: float
    trace: tuple[dict[str, Any], ...]
    metadata: dict[str, Any]


class MemoryConsolidationEngine:
    def consolidate(self, memories: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        merged: dict[str, dict[str, Any]] = {}
        forgotten: list[dict[str, Any]] = []
        for memory in memories:
            title = memory.get("title", "").strip().lower()
            if not title:
                continue
            current = merged.get(title)
            if current is None:
                merged[title] = dict(memory)
                continue
            current["confidence_score"] = round(max(current.get("confidence_score", 0.0), memory.get("confidence_score", 0.0)), 2)
            current["importance_score"] = round(max(current.get("importance_score", 0.0), memory.get("importance_score", 0.0)), 2)
            current["content"] = current.get("content", "")
            current["updated_at"] = memory.get("updated_at") or current.get("updated_at")
            current.setdefault("provenance", [])
            current["provenance"] = [*current["provenance"], memory.get("source", "memory")]
            if memory.get("confidence_score", 0.0) < 0.25 or memory.get("importance_score", 0.0) < 0.2:
                forgotten.append(memory)
        return list(merged.values()), forgotten


class ForgettingPolicy:
    def should_forget(self, memory: dict[str, Any], *, retention_days: int = 90, minimum_confidence: float = 0.25) -> bool:
        created_at = memory.get("created_at")
        confidence = float(memory.get("confidence_score", 0.0))
        if confidence < minimum_confidence:
            return True
        if created_at is None:
            return False
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at)
            except ValueError:
                return False
        if not isinstance(created_at, datetime):
            return False
        age_days = (datetime.now(timezone.utc) - created_at).days
        return age_days > retention_days and confidence < 0.7


class PreferenceEvolutionEngine:
    def evolve(self, memories: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        buckets: dict[str, dict[str, Any]] = {}
        expired: list[dict[str, Any]] = []
        for memory in memories:
            if memory.get("memory_type") != "semantic":
                continue
            key = memory.get("title", "").strip().lower()
            if not key:
                continue
            bucket = buckets.setdefault(key, dict(memory))
            bucket["confidence_score"] = round(max(bucket.get("confidence_score", 0.0), memory.get("confidence_score", 0.0)) + 0.05, 2)
            bucket["updated_at"] = memory.get("updated_at") or bucket.get("updated_at")
            if memory.get("confidence_score", 0.0) < 0.3:
                expired.append(memory)
        return list(buckets.values()), expired


class PatternDiscoveryEngine:
    def discover(self, learning_report: LearningReport, adaptive_report: AdaptivePlanningReport | None) -> tuple[dict[str, Any], ...]:
        patterns: list[dict[str, Any]] = []
        if learning_report.reusable_execution_patterns:
            patterns.extend({
                "pattern_type": "successful_execution_sequence",
                "title": pattern.title,
                "summary": pattern.summary,
                "confidence": pattern.confidence,
            } for pattern in learning_report.reusable_execution_patterns)
        if adaptive_report is not None:
            patterns.append({
                "pattern_type": "replanning_rationale",
                "title": "Adaptive replanning",
                "summary": adaptive_report.replanning_reason,
                "confidence": adaptive_report.planning_confidence,
            })
        return tuple(patterns)


class CapabilityScoringEngine:
    def score(self, memories: list[dict[str, Any]], patterns: tuple[dict[str, Any], ...]) -> dict[str, dict[str, float]]:
        scores: dict[str, dict[str, float]] = {}
        categories = ("Memory", "Knowledge", "RAG", "Workflow", "Tool Execution", "Provider", "Multi-Agent")
        for category in categories:
            related = [m for m in memories if category.lower().split()[0] in str(m.get("title", "")).lower() or category.lower().split()[0] in str(m.get("content", "")).lower()]
            success_rate = round(min(1.0, 0.35 + 0.1 * len(related)), 2)
            avg_latency = round(max(0.05, 1.5 - 0.05 * len(related)), 2)
            confidence = round(min(0.99, 0.4 + 0.08 * len(related)), 2)
            usage = float(len(related))
            failure_frequency = round(max(0.0, 1.0 - success_rate), 2)
            scores[category] = {
                "success_rate": success_rate,
                "average_latency": avg_latency,
                "confidence": confidence,
                "historical_usage": usage,
                "failure_frequency": failure_frequency,
            }
        return scores


class LongTermIntelligenceEngine:
    def __init__(
        self,
        *,
        memory_service: Any,
        capability_scoring_engine: CapabilityScoringEngine | None = None,
        pattern_discovery_engine: PatternDiscoveryEngine | None = None,
        preference_evolution_engine: PreferenceEvolutionEngine | None = None,
        memory_consolidation_engine: MemoryConsolidationEngine | None = None,
        forgetting_policy: ForgettingPolicy | None = None,
    ) -> None:
        self.memory_service = memory_service
        self.capability_scoring_engine = capability_scoring_engine or CapabilityScoringEngine()
        self.pattern_discovery_engine = pattern_discovery_engine or PatternDiscoveryEngine()
        self.preference_evolution_engine = preference_evolution_engine or PreferenceEvolutionEngine()
        self.memory_consolidation_engine = memory_consolidation_engine or MemoryConsolidationEngine()
        self.forgetting_policy = forgetting_policy or ForgettingPolicy()

    async def persist_intelligence(
        self,
        *,
        organization_id: int,
        agent_id: int,
        current_user: Any,
        learning_report: LearningReport,
        adaptive_report: AdaptivePlanningReport | None,
    ) -> LongTermIntelligenceReport:
        started_at = datetime.now(timezone.utc)
        if self.memory_service is None or not hasattr(self.memory_service, "list_memories"):
            completed_at = datetime.now(timezone.utc)
            report = LongTermIntelligenceReport(
                consolidated_memories=(),
                forgotten_memories=(),
                evolved_preferences=(),
                discovered_patterns=(),
                capability_scores={},
                long_term_knowledge=(),
                intelligence_confidence=0.5,
                persisted=False,
                started_at=started_at.isoformat(),
                completed_at=completed_at.isoformat(),
                duration=(completed_at - started_at).total_seconds(),
                trace=(
                    {"stage_name": "Long-Term Intelligence Started", "status": "SKIPPED", "summary": "MemoryService unavailable."},
                    {"stage_name": "Long-Term Intelligence Completed", "status": "SKIPPED", "summary": "No persistence performed."},
                ),
                metadata={
                    "organization_id": organization_id,
                    "agent_id": agent_id,
                    "long_term_knowledge_count": 0,
                },
            )
            await register_long_term_intelligence(
                str(organization_id),
                {
                    "organization_id": organization_id,
                    "agent_id": agent_id,
                    "consolidated_memories": [],
                    "forgotten_memories": [],
                    "evolved_preferences": [],
                    "discovered_patterns": [],
                    "capability_scores": {},
                    "intelligence_confidence": 0.5,
                    "trace": [entry for entry in report.trace],
                },
            )
            return report
        base_memories = list(self.memory_service.list_memories(organization_id, agent_id))
        memory_dicts = [memory if isinstance(memory, dict) else memory.__dict__ for memory in base_memories]
        consolidated_memories, forgotten_from_consolidation = self.memory_consolidation_engine.consolidate(memory_dicts)
        evolved_preferences, expired_preferences = self.preference_evolution_engine.evolve(consolidated_memories)
        discovered_patterns = self.pattern_discovery_engine.discover(learning_report, adaptive_report)
        capability_scores = self.capability_scoring_engine.score(evolved_preferences, discovered_patterns)
        forgotten_memories = [memory for memory in evolved_preferences if self.forgetting_policy.should_forget(memory)]
        intelligence_confidence = round(min(0.99, (learning_report.confidence + (adaptive_report.planning_confidence if adaptive_report else 0.5) + 0.5) / 3), 2)
        knowledge_records = (
            LongTermKnowledge(
                title="Execution strategy",
                summary=learning_report.summary,
                confidence=learning_report.confidence,
                knowledge_type="execution_strategy",
                provenance={"learning_report": learning_report.metadata.__dict__},
            ),
            LongTermKnowledge(
                title="Capability scores",
                summary="Persisted capability effectiveness statistics.",
                confidence=intelligence_confidence,
                knowledge_type="capability_statistics",
                provenance={"capability_scores": capability_scores},
            ),
        )
        if hasattr(self.memory_service, "create_memory"):
            for knowledge in knowledge_records:
                self.memory_service.create_memory(
                    org_id=organization_id,
                    agent_id=agent_id,
                    title=knowledge.title,
                    content=knowledge.summary,
                    memory_type="long_term",
                    importance_score=knowledge.confidence,
                    confidence_score=knowledge.confidence,
                    user_id=getattr(current_user, "id", agent_id),
                )
        completed_at = datetime.now(timezone.utc)
        report = LongTermIntelligenceReport(
            consolidated_memories=tuple(consolidated_memories),
            forgotten_memories=tuple(forgotten_memories + forgotten_from_consolidation + expired_preferences),
            evolved_preferences=tuple(evolved_preferences),
            discovered_patterns=discovered_patterns,
            capability_scores=capability_scores,
            long_term_knowledge=knowledge_records,
            intelligence_confidence=intelligence_confidence,
            persisted=True,
            started_at=started_at.isoformat(),
            completed_at=completed_at.isoformat(),
            duration=(completed_at - started_at).total_seconds(),
            trace=(
                {"stage_name": "Long-Term Intelligence Started", "status": "COMPLETED", "summary": "Long-term intelligence processing started."},
                {"stage_name": "Memory Consolidation", "status": "COMPLETED", "summary": f"Consolidated {len(consolidated_memories)} memory records."},
                {"stage_name": "Preference Evolution", "status": "COMPLETED", "summary": f"Evolved {len(evolved_preferences)} preferences."},
                {"stage_name": "Pattern Discovery", "status": "COMPLETED", "summary": f"Discovered {len(discovered_patterns)} patterns."},
                {"stage_name": "Capability Scoring", "status": "COMPLETED", "summary": "Capability statistics updated."},
                {"stage_name": "Intelligence Persisted", "status": "COMPLETED", "summary": "Long-term knowledge persisted."},
                {"stage_name": "Long-Term Intelligence Completed", "status": "COMPLETED", "summary": "Long-term intelligence completed."},
            ),
            metadata={
                "organization_id": organization_id,
                "agent_id": agent_id,
                "long_term_knowledge_count": len(knowledge_records),
            },
        )
        await register_long_term_intelligence(
            str(organization_id),
            {
                "organization_id": organization_id,
                "agent_id": agent_id,
                "consolidated_memories": list(report.consolidated_memories),
                "forgotten_memories": list(report.forgotten_memories),
                "evolved_preferences": list(report.evolved_preferences),
                "discovered_patterns": list(report.discovered_patterns),
                "capability_scores": report.capability_scores,
                "intelligence_confidence": report.intelligence_confidence,
                "trace": [entry for entry in report.trace],
            },
        )
        return report
