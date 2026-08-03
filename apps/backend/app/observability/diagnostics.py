"""
Diagnostics service for tracking active executions, sessions, and streams.
"""

import asyncio
from typing import Dict, Any, List

# Thread-safe in-memory maps for live tracking
active_executions: Dict[str, Dict[str, Any]] = {}
active_streams: Dict[str, Dict[str, Any]] = {}
active_sessions: Dict[str, Dict[str, Any]] = {}
active_workflows: Dict[str, Dict[str, Any]] = {}
active_cognitive_analyses: Dict[str, Dict[str, Any]] = {}
active_planning_runs: Dict[str, Dict[str, Any]] = {}
active_execution_engines: Dict[str, Dict[str, Any]] = {}
active_capability_events: Dict[str, Dict[str, Any]] = {}
active_reflection_reports: Dict[str, Dict[str, Any]] = {}
active_evaluation_reports: Dict[str, Dict[str, Any]] = {}
active_learning_reports: Dict[str, Dict[str, Any]] = {}
active_learning_policies: Dict[str, Dict[str, Any]] = {}
active_adaptive_plans: Dict[str, Dict[str, Any]] = {}
active_long_term_intelligence: Dict[str, Dict[str, Any]] = {}
active_runtime_optimizations: Dict[str, Dict[str, Any]] = {}
active_runtime_governance: Dict[str, Dict[str, Any]] = {}
active_goal_reports: Dict[str, Dict[str, Any]] = {}
active_goal_traces: Dict[str, Dict[str, Any]] = {}
active_task_reports: Dict[str, Dict[str, Any]] = {}
active_task_traces: Dict[str, Dict[str, Any]] = {}
active_autonomous_executions: Dict[str, Dict[str, Any]] = {}
active_multi_agent_orchestrations: Dict[str, Dict[str, Any]] = {}
last_cognitive_analysis: Dict[str, Any] | None = None
last_execution_blueprint: Dict[str, Any] | None = None
last_execution_context: Dict[str, Any] | None = None
last_execution_engine: Dict[str, Any] | None = None
last_capability_event: Dict[str, Any] | None = None
last_reflection_report: Dict[str, Any] | None = None
last_evaluation_report: Dict[str, Any] | None = None
last_learning_report: Dict[str, Any] | None = None
last_learning_policy: Dict[str, Any] | None = None
last_adaptive_plan: Dict[str, Any] | None = None
last_long_term_intelligence: Dict[str, Any] | None = None
last_runtime_optimization: Dict[str, Any] | None = None
last_runtime_governance: Dict[str, Any] | None = None
last_goal_report: Dict[str, Any] | None = None
last_goal_trace: Dict[str, Any] | None = None
last_task_report: Dict[str, Any] | None = None
last_task_trace: Dict[str, Any] | None = None
last_autonomous_execution: Dict[str, Any] | None = None
last_multi_agent_orchestration: Dict[str, Any] | None = None

_lock = asyncio.Lock()


async def register_execution(execution_id: str, metadata: Dict[str, Any]) -> None:
    async with _lock:
        active_executions[execution_id] = metadata


async def unregister_execution(execution_id: str) -> None:
    async with _lock:
        active_executions.pop(execution_id, None)


async def register_stream(stream_id: str, metadata: Dict[str, Any]) -> None:
    async with _lock:
        active_streams[stream_id] = metadata


async def unregister_stream(stream_id: str) -> None:
    async with _lock:
        active_streams.pop(stream_id, None)


async def register_session(session_id: str, metadata: Dict[str, Any]) -> None:
    async with _lock:
        active_sessions[session_id] = metadata


async def unregister_session(session_id: str) -> None:
    async with _lock:
        active_sessions.pop(session_id, None)


async def register_workflow(workflow_id: str, metadata: Dict[str, Any]) -> None:
    async with _lock:
        active_workflows[workflow_id] = metadata


async def unregister_workflow(workflow_id: str) -> None:
    async with _lock:
        active_workflows.pop(workflow_id, None)


async def register_cognitive_analysis(analysis_id: str, metadata: Dict[str, Any]) -> None:
    async with _lock:
        active_cognitive_analyses[analysis_id] = metadata
        global last_cognitive_analysis
        last_cognitive_analysis = metadata


async def unregister_cognitive_analysis(analysis_id: str) -> None:
    async with _lock:
        active_cognitive_analyses.pop(analysis_id, None)


async def register_planning_run(planning_id: str, metadata: Dict[str, Any]) -> None:
    async with _lock:
        active_planning_runs[planning_id] = metadata
        global last_execution_blueprint
        last_execution_blueprint = metadata


async def register_execution_context(context_id: str, metadata: Dict[str, Any]) -> None:
    async with _lock:
        global last_execution_context
        last_execution_context = metadata


async def register_execution_engine(execution_id: str, metadata: Dict[str, Any]) -> None:
    async with _lock:
        active_execution_engines[execution_id] = metadata
        global last_execution_engine
        last_execution_engine = metadata


async def register_capability_event(event_id: str, metadata: Dict[str, Any]) -> None:
    async with _lock:
        active_capability_events[event_id] = metadata
        global last_capability_event
        last_capability_event = metadata


async def register_reflection_report(report_id: str, metadata: Dict[str, Any]) -> None:
    async with _lock:
        active_reflection_reports[report_id] = metadata
        global last_reflection_report
        last_reflection_report = metadata


async def register_evaluation_report(report_id: str, metadata: Dict[str, Any]) -> None:
    async with _lock:
        active_evaluation_reports[report_id] = metadata
        global last_evaluation_report
        last_evaluation_report = metadata


async def register_learning_report(report_id: str, metadata: Dict[str, Any]) -> None:
    async with _lock:
        active_learning_reports[report_id] = metadata
        global last_learning_report
        last_learning_report = metadata


async def register_learning_policy(report_id: str, metadata: Dict[str, Any]) -> None:
    async with _lock:
        active_learning_policies[report_id] = metadata
        global last_learning_policy
        last_learning_policy = metadata


async def register_adaptive_plan(plan_id: str, metadata: Dict[str, Any]) -> None:
    async with _lock:
        active_adaptive_plans[plan_id] = metadata
        global last_adaptive_plan
        last_adaptive_plan = metadata


async def register_long_term_intelligence(intelligence_id: str, metadata: Dict[str, Any]) -> None:
    async with _lock:
        active_long_term_intelligence[intelligence_id] = metadata
        global last_long_term_intelligence
        last_long_term_intelligence = metadata


async def register_runtime_optimization(optimization_id: str, metadata: Dict[str, Any]) -> None:
    async with _lock:
        active_runtime_optimizations[optimization_id] = metadata
        global last_runtime_optimization
        last_runtime_optimization = metadata


async def register_runtime_governance(governance_id: str, metadata: Dict[str, Any]) -> None:
    async with _lock:
        active_runtime_governance[governance_id] = metadata
        global last_runtime_governance
        last_runtime_governance = metadata


async def register_goal_report(goal_id: str, metadata: Dict[str, Any]) -> None:
    async with _lock:
        active_goal_reports[goal_id] = metadata
        global last_goal_report
        last_goal_report = metadata


async def register_goal_trace(goal_id: str, metadata: Dict[str, Any]) -> None:
    async with _lock:
        active_goal_traces[goal_id] = metadata
        global last_goal_trace
        last_goal_trace = metadata


async def register_task_report(task_id: str, metadata: Dict[str, Any]) -> None:
    async with _lock:
        active_task_reports[task_id] = metadata
        global last_task_report
        last_task_report = metadata


async def register_task_trace(task_id: str, metadata: Dict[str, Any]) -> None:
    async with _lock:
        active_task_traces[task_id] = metadata
        global last_task_trace
        last_task_trace = metadata


async def register_autonomous_execution(execution_id: str, metadata: Dict[str, Any]) -> None:
    async with _lock:
        active_autonomous_executions[execution_id] = metadata
        global last_autonomous_execution
        last_autonomous_execution = metadata


async def register_multi_agent_orchestration(orchestration_id: str, metadata: Dict[str, Any]) -> None:
    async with _lock:
        active_multi_agent_orchestrations[orchestration_id] = metadata
        global last_multi_agent_orchestration
        last_multi_agent_orchestration = metadata


async def unregister_planning_run(planning_id: str) -> None:
    async with _lock:
        active_planning_runs.pop(planning_id, None)


async def get_diagnostics_snapshot() -> Dict[str, Any]:
    async with _lock:
        return {
            "active_executions_count": len(active_executions),
            "active_executions": list(active_executions.values()),
            "active_streams_count": len(active_streams),
            "active_streams": list(active_streams.values()),
            "active_sessions_count": len(active_sessions),
            "active_sessions": list(active_sessions.values()),
            "active_workflows_count": len(active_workflows),
            "active_workflows": list(active_workflows.values()),
            "active_cognitive_analyses_count": len(active_cognitive_analyses),
            "active_cognitive_analyses": list(active_cognitive_analyses.values()),
            "last_cognitive_analysis": last_cognitive_analysis,
            "active_planning_runs_count": len(active_planning_runs),
            "active_planning_runs": list(active_planning_runs.values()),
            "last_execution_blueprint": last_execution_blueprint,
            "last_execution_context": last_execution_context,
            "active_execution_engines_count": len(active_execution_engines),
            "active_execution_engines": list(active_execution_engines.values()),
            "last_execution_engine": last_execution_engine,
            "active_capability_events_count": len(active_capability_events),
            "active_capability_events": list(active_capability_events.values()),
            "last_capability_event": last_capability_event,
            "active_reflection_reports_count": len(active_reflection_reports),
            "active_reflection_reports": list(active_reflection_reports.values()),
            "last_reflection_report": last_reflection_report,
            "active_evaluation_reports_count": len(active_evaluation_reports),
            "active_evaluation_reports": list(active_evaluation_reports.values()),
            "last_evaluation_report": last_evaluation_report,
            "active_learning_reports_count": len(active_learning_reports),
            "active_learning_reports": list(active_learning_reports.values()),
            "last_learning_report": last_learning_report,
            "active_learning_policies_count": len(active_learning_policies),
            "active_learning_policies": list(active_learning_policies.values()),
            "last_learning_policy": last_learning_policy,
            "active_adaptive_plans_count": len(active_adaptive_plans),
            "active_adaptive_plans": list(active_adaptive_plans.values()),
            "last_adaptive_plan": last_adaptive_plan,
            "active_long_term_intelligence_count": len(active_long_term_intelligence),
            "active_long_term_intelligence": list(active_long_term_intelligence.values()),
            "last_long_term_intelligence": last_long_term_intelligence,
            "active_runtime_optimizations_count": len(active_runtime_optimizations),
            "active_runtime_optimizations": list(active_runtime_optimizations.values()),
            "last_runtime_optimization": last_runtime_optimization,
            "active_runtime_governance_count": len(active_runtime_governance),
            "active_runtime_governance": list(active_runtime_governance.values()),
            "last_runtime_governance": last_runtime_governance,
            "active_goal_reports_count": len(active_goal_reports),
            "active_goal_reports": list(active_goal_reports.values()),
            "last_goal_report": last_goal_report,
            "active_goal_traces_count": len(active_goal_traces),
            "active_goal_traces": list(active_goal_traces.values()),
            "last_goal_trace": last_goal_trace,
            "active_task_reports_count": len(active_task_reports),
            "active_task_reports": list(active_task_reports.values()),
            "last_task_report": last_task_report,
            "active_task_traces_count": len(active_task_traces),
            "active_task_traces": list(active_task_traces.values()),
            "last_task_trace": last_task_trace,
            "active_autonomous_executions_count": len(active_autonomous_executions),
            "active_autonomous_executions": list(active_autonomous_executions.values()),
            "last_autonomous_execution": last_autonomous_execution,
            "active_multi_agent_orchestrations_count": len(active_multi_agent_orchestrations),
            "active_multi_agent_orchestrations": list(active_multi_agent_orchestrations.values()),
            "last_multi_agent_orchestration": last_multi_agent_orchestration,
        }
