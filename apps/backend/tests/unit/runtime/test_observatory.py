"""Unit tests for the runtime observatory platform."""

from __future__ import annotations

import asyncio

from app.runtime.observatory import RuntimeObservatoryEngine
from app.services.observability_service import ObservabilityService


def _runtime_context() -> dict:
    return {
        "runtime_version": "AgentCorp V2",
        "execution_context": {"execution_metadata": {"execution_id": "exec-1", "request_id": "req-1"}},
        "cognitive_state": {"request_id": "req-1"},
        "execution_blueprint": {"task_graph": [{"identifier": "task-1"}]},
        "goal_report": {"goal_id": "goal-1"},
        "task_reports": [{"task_id": "task-1"}],
        "reflection_report": {"summary": "reflected"},
        "evaluation_report": {"summary": "evaluated"},
        "learning_report": {"summary": "learned"},
        "adaptive_plan": {"summary": "adapted"},
        "long_term_intelligence": {"intelligence_confidence": 0.9},
        "runtime_optimization": {"estimated_improvement": 0.2},
        "runtime_governance": {"decision": {"allowed": True}},
        "multi_agent_orchestrator": {"worker_agent_ids": [2, 3]},
        "memory": {"id": 1},
        "knowledge": {"id": 2},
        "rag": {"id": 3},
        "workflow": {"id": 4},
        "tool_execution": {"id": 5},
        "provider": {"name": "mock"},
        "prompt_builder": {"id": 6},
        "execution_engine": {"id": 7},
        "capability_dispatcher": {"id": 8},
        "native_executors": [{"name": "native"}],
        "business_services": [{"name": "business"}],
        "repositories": [{"name": "repo"}],
        "persistence": {"name": "persist"},
        "response": {"id": 9},
        "active_goals": [{"goal_id": "goal-1"}],
        "active_tasks": [{"task_id": "task-1"}],
        "execution_trace": [
            {"stage_name": "Request Received", "status": "COMPLETED", "summary": "accepted", "started_at": "2026-08-02T00:00:00+00:00", "completed_at": "2026-08-02T00:00:01+00:00", "duration_seconds": 1.0},
            {"stage_name": "Execution Engine", "status": "COMPLETED", "summary": "ran", "started_at": "2026-08-02T00:00:01+00:00", "completed_at": "2026-08-02T00:00:02+00:00", "duration_seconds": 1.0},
        ],
        "provider_name": "mock",
        "model": "mock-model",
        "streaming": [{"stream_id": "stream-1"}],
        "capability_scores": {"provider": {"success_rate": 1.0}},
        "preferences": [{"title": "communication"}],
        "supervisor_agent": {"id": 1},
        "worker_agents": [{"id": 2}],
        "delegated_tasks": [{"task_id": "task-1"}],
        "aggregated_results": [{"task_id": "task-1"}],
    }


def test_runtime_observatory_engine_builds_graphs_and_snapshot() -> None:
    engine = RuntimeObservatoryEngine()
    context = _runtime_context()
    graph = engine.build_runtime_graph(runtime_context=context)
    execution_graph = engine.build_execution_graph(runtime_context=context)
    timeline = engine.build_timeline(trace=context["execution_trace"])
    snapshot = engine.build_snapshot(runtime_context=context)

    assert any(node["id"] == "runtime_governance" for node in graph["nodes"])
    assert any(edge["source"] == "runtime_optimization" for edge in graph["edges"])
    assert execution_graph["nodes"][0]["label"] == "Execution Engine"
    assert timeline[0]["stage_name"] == "Request Received"
    assert snapshot["runtime_version"] == "AgentCorp V2"
    assert snapshot["runtime_graph"]["nodes"]


def test_runtime_observatory_search_filters_deterministically() -> None:
    engine = RuntimeObservatoryEngine()
    context = _runtime_context()
    result = engine.search(runtime_context=context, request_id="req-1", provider="mock")
    assert result["query"]["request_id"] == "req-1"
    assert result["matches"]


def test_runtime_observatory_service_exposes_snapshot_and_search() -> None:
    service = ObservabilityService.__new__(ObservabilityService)

    async def fake_get_diagnostics():
        return {
            "last_execution_context": {"execution_context": {"runtime_version": "AgentCorp V2", "execution_metadata": {"execution_id": "exec-1", "request_id": "req-1"}}},
            "last_cognitive_analysis": {"cognitive_state": {"request_id": "req-1"}},
            "last_execution_blueprint": {"task_graph": []},
            "last_goal_report": {"goal_id": "goal-1"},
            "active_goal_reports": [{"goal_id": "goal-1"}],
            "active_task_reports": [{"task_id": "task-1"}],
            "last_reflection_report": {"summary": "reflected"},
            "last_evaluation_report": {"summary": "evaluated"},
            "last_learning_report": {"summary": "learned"},
            "last_adaptive_plan": {"summary": "adapted"},
            "last_long_term_intelligence": {"intelligence_confidence": 0.9, "capability_scores": {"provider": {"success_rate": 1.0}}},
            "last_runtime_optimization": {"estimated_improvement": 0.2},
            "last_runtime_governance": {"decision": {"allowed": True}},
            "last_multi_agent_orchestration": {"worker_agent_ids": [2]},
            "active_streams": [{"stream_id": "stream-1"}],
            "active_workflows": [{"workflow_id": "workflow-1"}],
            "active_capability_events": [{"capability": "provider"}],
            "active_execution_engines": [{"execution_id": "exec-1"}],
            "last_execution_engine": {"provider": "mock", "model": "mock-model", "execution_trace": [{"stage_name": "Execution Engine"}], "execution_initialized": True, "execution_state": "COMPLETED", "current_task": {}, "completed_tasks": [], "pending_tasks": [], "execution_timeline": [], "execution_results": []},
            "active_autonomous_executions": [],
            "active_goal_traces": [{"goal_id": "goal-1"}],
            "active_task_traces": [{"task_id": "task-1"}],
        }

    async def fake_get_traces():
        return [{"name": "runtime_router.chat"}]

    service.get_diagnostics = fake_get_diagnostics  # type: ignore[method-assign]
    service.get_active_traces = fake_get_traces  # type: ignore[method-assign]

    observatory = asyncio.run(service.get_runtime_observatory())
    assert observatory["runtime_snapshot"]["runtime_version"] == "AgentCorp V2"
    search = asyncio.run(service.search_runtime_observability(request_id="req-1"))
    assert search["query"]["request_id"] == "req-1"
