"""
Runtime V2 observatory platform.

Read-only aggregation layer for runtime graphs, timeline views, snapshots,
and deterministic search over already-collected observability state.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class ObservatoryNode:
    node_id: str
    label: str
    object_ref: Any
    metadata: dict[str, Any]


@dataclass(frozen=True)
class ObservatoryEdge:
    source: str
    target: str
    relation: str


@dataclass(frozen=True)
class TimelineEntry:
    stage_name: str
    started_at: str | None
    completed_at: str | None
    duration_seconds: float | None
    parent_stage: str | None
    child_stages: tuple[str, ...]
    status: str | None
    summary: str | None
    raw: dict[str, Any]


class RuntimeObservatoryEngine:
    def build_runtime_graph(self, *, runtime_context: dict[str, Any]) -> dict[str, Any]:
        nodes: list[ObservatoryNode] = []
        edges: list[ObservatoryEdge] = []

        def add_node(node_id: str, label: str, ref: Any, **metadata: Any) -> None:
            nodes.append(ObservatoryNode(node_id=node_id, label=label, object_ref=ref, metadata=metadata))

        def add_edge(source: str, target: str, relation: str) -> None:
            edges.append(ObservatoryEdge(source=source, target=target, relation=relation))

        execution_context = runtime_context.get("execution_context")
        cognitive_state = runtime_context.get("cognitive_state")
        execution_blueprint = runtime_context.get("execution_blueprint")
        goal_report = runtime_context.get("goal_report")
        task_reports = runtime_context.get("task_reports", [])
        reflection_report = runtime_context.get("reflection_report")
        evaluation_report = runtime_context.get("evaluation_report")
        learning_report = runtime_context.get("learning_report")
        adaptive_plan = runtime_context.get("adaptive_plan")
        long_term_intelligence = runtime_context.get("long_term_intelligence")
        runtime_optimization = runtime_context.get("runtime_optimization")
        runtime_governance = runtime_context.get("runtime_governance")
        multi_agent = runtime_context.get("multi_agent_orchestrator")
        memory = runtime_context.get("memory")
        knowledge = runtime_context.get("knowledge")
        rag = runtime_context.get("rag")
        workflow = runtime_context.get("workflow")
        tool_execution = runtime_context.get("tool_execution")
        provider = runtime_context.get("provider")
        prompt_builder = runtime_context.get("prompt_builder")

        add_node("runtime_version", "Runtime Version", runtime_context.get("runtime_version"), value=runtime_context.get("runtime_version"))
        add_node("execution_context", "Execution Context", execution_context, execution_metadata=getattr(execution_context, "execution_metadata", None))
        add_node("cognitive_state", "Cognitive State", cognitive_state, required_capabilities=getattr(cognitive_state, "required_runtime_capabilities", ()))
        add_node("execution_blueprint", "Execution Blueprint", execution_blueprint, task_graph=getattr(execution_blueprint, "task_graph", ()))
        add_node("goal", "Goal", goal_report, goal_id=getattr(goal_report, "goal_id", None))
        add_node("tasks", "Tasks", task_reports, count=len(task_reports))
        add_node("reflection", "Reflection", reflection_report, confidence=getattr(reflection_report, "confidence", None))
        add_node("evaluation", "Evaluation", evaluation_report, confidence=getattr(evaluation_report, "confidence", None))
        add_node("learning", "Learning", learning_report, confidence=getattr(learning_report, "confidence", None))
        add_node("adaptive_planning", "Adaptive Planning", adaptive_plan, planning_confidence=getattr(adaptive_plan, "planning_confidence", None))
        add_node("long_term_intelligence", "Long-Term Intelligence", long_term_intelligence, intelligence_confidence=getattr(long_term_intelligence, "intelligence_confidence", None))
        add_node("runtime_optimization", "Runtime Optimization", runtime_optimization, estimated_improvement=getattr(runtime_optimization, "estimated_improvement", None))
        add_node("runtime_governance", "Governance", runtime_governance, decision=getattr(getattr(runtime_governance, "decision", None), "allowed", None))
        add_node("multi_agent_orchestrator", "Multi-Agent Orchestrator", multi_agent, participant_count=len(getattr(multi_agent, "worker_agent_ids", ()) or ()))
        add_node("memory", "Memory", memory, source="memory_service")
        add_node("knowledge", "Knowledge", knowledge, source="knowledge_service")
        add_node("rag", "RAG", rag, source="rag_service")
        add_node("workflow", "Workflow", workflow, source="workflow_service")
        add_node("tool_execution", "Tool Execution", tool_execution, source="tool_execution_service")
        add_node("provider", "Provider", provider, source="provider_service")
        add_node("prompt_builder", "Prompt Builder", prompt_builder, source="prompt_builder")

        add_edge("runtime_version", "execution_context", "drives")
        add_edge("execution_context", "cognitive_state", "contains")
        add_edge("cognitive_state", "execution_blueprint", "produces")
        add_edge("goal", "tasks", "decomposes_into")
        add_edge("tasks", "execution_blueprint", "informs")
        add_edge("execution_blueprint", "execution_context", "shapes")
        add_edge("execution_context", "reflection", "yields")
        add_edge("reflection", "evaluation", "feeds")
        add_edge("evaluation", "learning", "feeds")
        add_edge("learning", "adaptive_planning", "feeds")
        add_edge("adaptive_planning", "long_term_intelligence", "feeds")
        add_edge("long_term_intelligence", "runtime_optimization", "feeds")
        add_edge("runtime_optimization", "runtime_governance", "precedes")
        add_edge("runtime_governance", "execution_context", "supervises")
        add_edge("multi_agent_orchestrator", "goal", "supervises")
        add_edge("memory", "long_term_intelligence", "supports")
        add_edge("knowledge", "rag", "supports")
        add_edge("rag", "learning", "supports")
        add_edge("workflow", "tool_execution", "coordinates")
        add_edge("prompt_builder", "provider", "prepares")
        add_edge("provider", "execution_context", "responds_to")

        return {
            "nodes": [node.__dict__ for node in nodes],
            "edges": [edge.__dict__ for edge in edges],
        }

    def build_execution_graph(self, *, runtime_context: dict[str, Any]) -> dict[str, Any]:
        execution_engine = runtime_context.get("execution_engine")
        capability_dispatcher = runtime_context.get("capability_dispatcher")
        native_executors = runtime_context.get("native_executors")
        business_services = runtime_context.get("business_services", [])
        repositories = runtime_context.get("repositories", [])
        persistence = runtime_context.get("persistence")
        response = runtime_context.get("response")
        return {
            "nodes": [
                {"id": "execution_engine", "label": "Execution Engine", "object": execution_engine},
                {"id": "capability_dispatcher", "label": "Capability Dispatcher", "object": capability_dispatcher},
                {"id": "native_executors", "label": "Native Executors", "object": native_executors},
                {"id": "business_services", "label": "Business Services", "object": business_services},
                {"id": "repositories", "label": "Repositories", "object": repositories},
                {"id": "persistence", "label": "Persistence", "object": persistence},
                {"id": "response", "label": "Response", "object": response},
            ],
            "edges": [
                {"source": "execution_engine", "target": "capability_dispatcher", "relation": "dispatches"},
                {"source": "capability_dispatcher", "target": "native_executors", "relation": "routes_to"},
                {"source": "native_executors", "target": "business_services", "relation": "calls"},
                {"source": "business_services", "target": "repositories", "relation": "persists_through"},
                {"source": "repositories", "target": "persistence", "relation": "stores"},
                {"source": "persistence", "target": "response", "relation": "produces"},
            ],
        }

    def build_memory_graph(self, *, runtime_context: dict[str, Any]) -> dict[str, Any]:
        return {
            "nodes": [
                {"id": "memory", "label": "Memory", "object": runtime_context.get("memory")},
                {"id": "knowledge", "label": "Knowledge", "object": runtime_context.get("knowledge")},
                {"id": "rag", "label": "RAG", "object": runtime_context.get("rag")},
                {"id": "learning", "label": "Learning", "object": runtime_context.get("learning_report")},
                {"id": "long_term_intelligence", "label": "Long-Term Intelligence", "object": runtime_context.get("long_term_intelligence")},
                {"id": "preferences", "label": "Preferences", "object": runtime_context.get("preferences")},
                {"id": "capability_scores", "label": "Capability Scores", "object": runtime_context.get("capability_scores")},
            ],
            "edges": [
                {"source": "memory", "target": "knowledge", "relation": "feeds"},
                {"source": "knowledge", "target": "rag", "relation": "retrieved_by"},
                {"source": "rag", "target": "learning", "relation": "informs"},
                {"source": "learning", "target": "long_term_intelligence", "relation": "persists"},
                {"source": "long_term_intelligence", "target": "preferences", "relation": "evolves"},
                {"source": "long_term_intelligence", "target": "capability_scores", "relation": "scores"},
            ],
        }

    def build_provider_graph(self, *, runtime_context: dict[str, Any]) -> dict[str, Any]:
        return {
            "nodes": [
                {"id": "prompt_builder", "label": "Prompt Builder", "object": runtime_context.get("prompt_builder")},
                {"id": "provider", "label": "Provider", "object": runtime_context.get("provider")},
                {"id": "model", "label": "Model", "object": runtime_context.get("model")},
                {"id": "tool_calls", "label": "Tool Calls", "object": runtime_context.get("tool_calls")},
                {"id": "streaming", "label": "Streaming", "object": runtime_context.get("streaming")},
                {"id": "response", "label": "Response", "object": runtime_context.get("response")},
            ],
            "edges": [
                {"source": "prompt_builder", "target": "provider", "relation": "prepares"},
                {"source": "provider", "target": "model", "relation": "selects"},
                {"source": "model", "target": "tool_calls", "relation": "emits"},
                {"source": "tool_calls", "target": "streaming", "relation": "feeds"},
                {"source": "streaming", "target": "response", "relation": "returns"},
            ],
        }

    def build_goal_graph(self, *, runtime_context: dict[str, Any]) -> dict[str, Any]:
        return {
            "nodes": [
                {"id": "goal", "label": "Goal", "object": runtime_context.get("goal_report")},
                {"id": "planning", "label": "Planning", "object": runtime_context.get("execution_blueprint")},
                {"id": "tasks", "label": "Tasks", "object": runtime_context.get("task_reports", [])},
                {"id": "execution", "label": "Execution", "object": runtime_context.get("execution_engine")},
                {"id": "completion", "label": "Completion", "object": runtime_context.get("response")},
                {"id": "reflection", "label": "Reflection", "object": runtime_context.get("reflection_report")},
                {"id": "evaluation", "label": "Evaluation", "object": runtime_context.get("evaluation_report")},
                {"id": "learning", "label": "Learning", "object": runtime_context.get("learning_report")},
            ],
            "edges": [
                {"source": "goal", "target": "planning", "relation": "creates"},
                {"source": "planning", "target": "tasks", "relation": "decomposes"},
                {"source": "tasks", "target": "execution", "relation": "drives"},
                {"source": "execution", "target": "completion", "relation": "produces"},
                {"source": "completion", "target": "reflection", "relation": "evaluated_by"},
                {"source": "reflection", "target": "evaluation", "relation": "feeds"},
                {"source": "evaluation", "target": "learning", "relation": "feeds"},
            ],
        }

    def build_multi_agent_graph(self, *, runtime_context: dict[str, Any]) -> dict[str, Any]:
        orchestrator = runtime_context.get("multi_agent_orchestrator")
        supervisor = runtime_context.get("supervisor_agent")
        worker_agents = runtime_context.get("worker_agents", [])
        delegated_tasks = runtime_context.get("delegated_tasks", [])
        aggregated_results = runtime_context.get("aggregated_results", [])
        return {
            "nodes": [
                {"id": "supervisor", "label": "Supervisor", "object": supervisor},
                {"id": "workers", "label": "Workers", "object": worker_agents},
                {"id": "delegation", "label": "Delegation", "object": delegated_tasks},
                {"id": "execution", "label": "Execution", "object": runtime_context.get("execution_engine")},
                {"id": "aggregation", "label": "Aggregation", "object": aggregated_results},
                {"id": "orchestrator", "label": "Multi-Agent Orchestrator", "object": orchestrator},
            ],
            "edges": [
                {"source": "supervisor", "target": "delegation", "relation": "assigns"},
                {"source": "delegation", "target": "workers", "relation": "routes_to"},
                {"source": "workers", "target": "execution", "relation": "executes"},
                {"source": "execution", "target": "aggregation", "relation": "produces"},
                {"source": "aggregation", "target": "orchestrator", "relation": "returns"},
            ],
        }

    def build_timeline(self, *, trace: list[dict[str, Any]]) -> list[dict[str, Any]]:
        entries: list[TimelineEntry] = []
        for index, item in enumerate(trace):
            children = tuple(
                other.get("stage_name")
                for other in trace[index + 1 : index + 2]
                if other.get("stage_name")
            )
            entries.append(
                TimelineEntry(
                    stage_name=item.get("stage_name", "unknown"),
                    started_at=item.get("started_at"),
                    completed_at=item.get("completed_at"),
                    duration_seconds=item.get("duration_seconds"),
                    parent_stage=trace[index - 1].get("stage_name") if index > 0 else None,
                    child_stages=children,
                    status=item.get("status"),
                    summary=item.get("summary"),
                    raw=item,
                )
            )
        return [entry.__dict__ for entry in entries]

    def build_snapshot(self, *, runtime_context: dict[str, Any]) -> dict[str, Any]:
        trace = runtime_context.get("execution_trace", [])
        return {
            "runtime_version": runtime_context.get("runtime_version"),
            "execution_context": runtime_context.get("execution_context"),
            "active_goals": runtime_context.get("active_goals", []),
            "active_tasks": runtime_context.get("active_tasks", []),
            "runtime_graph": self.build_runtime_graph(runtime_context=runtime_context),
            "execution_graph": self.build_execution_graph(runtime_context=runtime_context),
            "timeline": self.build_timeline(trace=trace),
            "observability_metadata": {
                "captured_at": datetime.now(timezone.utc).isoformat(),
                "source": "runtime_observatory",
            },
        }

    def search(self, *, runtime_context: dict[str, Any], request_id: str | None = None, execution_id: str | None = None, goal_id: str | None = None, task_id: str | None = None, runtime_version: str | None = None, provider: str | None = None, workflow: str | None = None, capability: str | None = None) -> dict[str, Any]:
        snapshot = self.build_snapshot(runtime_context=runtime_context)
        matches: list[dict[str, Any]] = []
        search_space = snapshot["timeline"] + snapshot["runtime_graph"]["nodes"] + snapshot["execution_graph"]["nodes"]
        for item in search_space:
            raw = item.get("raw") if isinstance(item, dict) else None
            candidate = raw or item
            if request_id and request_id not in str(candidate):
                continue
            if execution_id and execution_id not in str(candidate):
                continue
            if goal_id and goal_id not in str(candidate):
                continue
            if task_id and task_id not in str(candidate):
                continue
            if runtime_version and runtime_version not in str(candidate):
                continue
            if provider and provider not in str(candidate):
                continue
            if workflow and workflow not in str(candidate):
                continue
            if capability and capability not in str(candidate):
                continue
            matches.append(item)
        return {"query": {k: v for k, v in {
            "request_id": request_id,
            "execution_id": execution_id,
            "goal_id": goal_id,
            "task_id": task_id,
            "runtime_version": runtime_version,
            "provider": provider,
            "workflow": workflow,
            "capability": capability,
        }.items() if v is not None}, "matches": matches, "snapshot": snapshot}
