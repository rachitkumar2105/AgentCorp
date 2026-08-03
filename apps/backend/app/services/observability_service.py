"""
Observability and dashboard operations service.
"""

from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.observability.health import check_dependency_health
from app.observability.diagnostics import get_diagnostics_snapshot
from app.observability.metrics import backend_instance
from app.observability.tracing import tracer
from app.runtime.observatory import RuntimeObservatoryEngine
from app.repositories.metric_repository import MetricRepository, OperationLogRepository
from app.services.base_service import BaseService


class ObservabilityService(BaseService[MetricRepository]):
    """
    Main aggregator service for system observability.
    Queries metrics, traces, active diagnostics, and dependency status.
    """

    def __init__(self, repository: MetricRepository, operation_log_repo: OperationLogRepository):
        super().__init__(repository)
        self.operation_log_repo = operation_log_repo
        self.runtime_observatory_engine = RuntimeObservatoryEngine()
        self._last_diagnostics_cache: Dict[str, Any] | None = None
        self._last_traces_cache: List[Dict[str, Any]] | None = None

    async def get_health_status(self) -> Dict[str, Any]:
        """Verify health of dependencies."""
        return await check_dependency_health()

    async def get_diagnostics(self) -> Dict[str, Any]:
        """Fetch current diagnostics snapshot."""
        return await get_diagnostics_snapshot()

    async def get_metrics_dashboard(self) -> Dict[str, Any]:
        """Fetch system-wide metric values snapshot."""
        return await backend_instance.get_metrics_snapshot()

    async def get_active_traces(self) -> List[Dict[str, Any]]:
        """Fetch trace spans recorded."""
        return tracer.finished_spans

    async def get_runtime_observatory(self) -> Dict[str, Any]:
        """Return a live observability snapshot for runtime execution."""
        diagnostics = await self.get_diagnostics()
        traces = await self.get_active_traces()
        self._last_diagnostics_cache = diagnostics
        self._last_traces_cache = traces
        runtime_context = self._build_runtime_context(diagnostics=diagnostics, traces=traces)
        snapshot = self.runtime_observatory_engine.build_snapshot(runtime_context=runtime_context)
        return {
            "request_details": {
                "conversation_id": None,
                "user_id": None,
                "organization_id": None,
                "runtime_version": None,
                "provider": None,
                "model": None,
                "streaming_enabled": None,
                "execution_duration_ms": None,
                "request_status": "unknown",
            },
            "live_pipeline": diagnostics,
            "cognitive_analysis": diagnostics.get("last_cognitive_analysis"),
            "execution_blueprint": diagnostics.get("last_execution_blueprint"),
            "execution_engine": diagnostics.get("last_execution_engine"),
            "execution_initialized": (diagnostics.get("last_execution_engine") or {}).get("execution_initialized", False),
            "execution_state": (diagnostics.get("last_execution_engine") or {}).get("execution_state"),
            "current_task": (diagnostics.get("last_execution_engine") or {}).get("current_task"),
            "completed_tasks": (diagnostics.get("last_execution_engine") or {}).get("completed_tasks", []),
            "pending_tasks": (diagnostics.get("last_execution_engine") or {}).get("pending_tasks", []),
            "execution_timeline": (diagnostics.get("last_execution_engine") or {}).get("execution_timeline", []),
            "execution_results": (diagnostics.get("last_execution_engine") or {}).get("execution_results", []),
            "capability_resolution": diagnostics.get("last_capability_event"),
            "capability_events": diagnostics.get("active_capability_events", []),
            "reflection_report": diagnostics.get("last_reflection_report"),
            "reflection_reports": diagnostics.get("active_reflection_reports", []),
            "evaluation_report": diagnostics.get("last_evaluation_report"),
            "evaluation_reports": diagnostics.get("active_evaluation_reports", []),
            "learning_report": diagnostics.get("last_learning_report"),
            "learning_reports": diagnostics.get("active_learning_reports", []),
            "learning_policy": diagnostics.get("last_learning_policy"),
            "learning_policies": diagnostics.get("active_learning_policies", []),
            "adaptive_plan": diagnostics.get("last_adaptive_plan"),
            "adaptive_plans": diagnostics.get("active_adaptive_plans", []),
            "long_term_intelligence": diagnostics.get("last_long_term_intelligence"),
            "long_term_intelligences": diagnostics.get("active_long_term_intelligence", []),
            "runtime_optimization": diagnostics.get("last_runtime_optimization"),
            "runtime_optimizations": diagnostics.get("active_runtime_optimizations", []),
            "runtime_governance": diagnostics.get("last_runtime_governance"),
            "runtime_governances": diagnostics.get("active_runtime_governance", []),
            "goal_report": diagnostics.get("last_goal_report"),
            "goal_reports": diagnostics.get("active_goal_reports", []),
            "goal_trace": diagnostics.get("last_goal_trace"),
            "goal_traces": diagnostics.get("active_goal_traces", []),
            "task_report": diagnostics.get("last_task_report"),
            "task_reports": diagnostics.get("active_task_reports", []),
            "task_trace": diagnostics.get("last_task_trace"),
            "task_traces": diagnostics.get("active_task_traces", []),
            "task_queue_state": diagnostics.get("last_task_report"),
            "autonomous_execution": diagnostics.get("last_autonomous_execution"),
            "autonomous_executions": diagnostics.get("active_autonomous_executions", []),
            "timeline": traces,
            "runtime_graph": snapshot["runtime_graph"],
            "execution_graph": snapshot["execution_graph"],
            "goal_graph": self.get_goal_graph(runtime_context),
            "task_graph": self.get_task_graph(runtime_context),
            "memory_graph": self.get_memory_graph(runtime_context),
            "provider_graph": self.get_provider_graph(runtime_context),
            "multi_agent_graph": self.get_multi_agent_graph(runtime_context),
            "runtime_snapshot": snapshot,
            "architecture": self.get_runtime_architecture(),
        }

    def get_runtime_architecture(self) -> Dict[str, Any]:
        """Return a static architecture graph based on the actual runtime layering."""
        return {
            "nodes": [
                {"id": "api", "label": "API"},
                {"id": "dependencies", "label": "Dependencies"},
                {"id": "runtime_router", "label": "Runtime Router"},
                {"id": "runtime", "label": "Runtime"},
                {"id": "execution_context", "label": "Execution Context"},
                {"id": "execution_engine", "label": "Execution Engine"},
                {"id": "state_machine", "label": "Execution State Machine"},
                {"id": "capability_dispatcher", "label": "Capability Dispatcher"},
                {"id": "capability_registry", "label": "Capability Registry"},
                {"id": "capability_runtime", "label": "Capability Runtime Layer"},
                {"id": "runtime_v1_adapter", "label": "Runtime V1 Adapter"},
                {"id": "memory", "label": "Memory"},
                {"id": "knowledge", "label": "Knowledge"},
                {"id": "rag", "label": "RAG"},
                {"id": "prompt_builder", "label": "Prompt Builder"},
                {"id": "goal_management", "label": "Goal Management"},
                {"id": "task_management", "label": "Task Management"},
                {"id": "autonomous_execution", "label": "Autonomous Execution"},
                {"id": "adaptive_planning", "label": "Adaptive Planning"},
                {"id": "runtime_optimization", "label": "Runtime Optimization"},
                {"id": "runtime_governance", "label": "Runtime Governance"},
                {"id": "long_term_intelligence", "label": "Long-Term Intelligence"},
                {"id": "provider", "label": "Provider"},
                {"id": "tools", "label": "Tools"},
                {"id": "workflow", "label": "Workflow"},
                {"id": "agent", "label": "Agent"},
                {"id": "persistence", "label": "Persistence"},
            ],
            "edges": [
                ("api", "dependencies"),
                ("dependencies", "runtime_router"),
                ("runtime_router", "runtime"),
                ("runtime", "execution_context"),
                ("execution_context", "execution_engine"),
                ("execution_engine", "state_machine"),
                ("state_machine", "capability_dispatcher"),
                ("capability_dispatcher", "capability_registry"),
                ("capability_registry", "capability_runtime"),
                ("capability_dispatcher", "runtime_v1_adapter"),
                ("runtime_v1_adapter", "memory"),
                ("runtime", "memory"),
                ("runtime", "knowledge"),
                ("runtime", "rag"),
                ("runtime", "prompt_builder"),
                ("runtime", "goal_management"),
                ("runtime", "task_management"),
                ("runtime", "autonomous_execution"),
                ("runtime", "adaptive_planning"),
                ("adaptive_planning", "runtime_optimization"),
                ("runtime_optimization", "long_term_intelligence"),
                ("runtime", "runtime_governance"),
                ("runtime_governance", "execution_context"),
                ("runtime", "long_term_intelligence"),
                ("runtime", "provider"),
                ("runtime", "tools"),
                ("runtime", "workflow"),
                ("runtime", "agent"),
                ("runtime", "persistence"),
            ],
        }

    def _build_runtime_context(self, *, diagnostics: Dict[str, Any], traces: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "runtime_version": diagnostics.get("last_execution_context", {}).get("execution_context", {}).get("runtime_version"),
            "execution_context": diagnostics.get("last_execution_context"),
            "cognitive_state": diagnostics.get("last_cognitive_analysis", {}).get("cognitive_state") if isinstance(diagnostics.get("last_cognitive_analysis"), dict) else diagnostics.get("last_cognitive_analysis"),
            "execution_blueprint": diagnostics.get("last_execution_blueprint"),
            "goal_report": diagnostics.get("last_goal_report"),
            "task_reports": diagnostics.get("active_task_reports", []),
            "reflection_report": diagnostics.get("last_reflection_report"),
            "evaluation_report": diagnostics.get("last_evaluation_report"),
            "learning_report": diagnostics.get("last_learning_report"),
            "adaptive_plan": diagnostics.get("last_adaptive_plan"),
            "long_term_intelligence": diagnostics.get("last_long_term_intelligence"),
            "runtime_optimization": diagnostics.get("last_runtime_optimization"),
            "runtime_governance": diagnostics.get("last_runtime_governance"),
            "multi_agent_orchestrator": diagnostics.get("last_multi_agent_orchestration"),
            "memory": diagnostics.get("last_long_term_intelligence"),
            "knowledge": diagnostics.get("last_long_term_intelligence"),
            "rag": diagnostics.get("last_learning_report"),
            "workflow": diagnostics.get("active_workflows", []),
            "tool_execution": diagnostics.get("last_execution_engine"),
            "provider": diagnostics.get("last_execution_engine"),
            "prompt_builder": diagnostics.get("last_execution_context"),
            "execution_engine": diagnostics.get("last_execution_engine"),
            "capability_dispatcher": diagnostics.get("last_execution_engine"),
            "native_executors": diagnostics.get("active_capability_events", []),
            "business_services": diagnostics.get("active_execution_engines", []),
            "repositories": diagnostics.get("active_execution_engines", []),
            "persistence": diagnostics.get("last_long_term_intelligence"),
            "response": diagnostics.get("last_execution_context"),
            "active_goals": diagnostics.get("active_goal_reports", []),
            "active_tasks": diagnostics.get("active_task_reports", []),
            "execution_trace": traces,
            "provider_name": (diagnostics.get("last_execution_engine") or {}).get("provider"),
            "model": (diagnostics.get("last_execution_engine") or {}).get("model"),
            "streaming": diagnostics.get("active_streams", []),
            "capability_scores": (diagnostics.get("last_long_term_intelligence") or {}).get("capability_scores", {}),
            "preferences": (diagnostics.get("last_long_term_intelligence") or {}).get("evolved_preferences", []),
            "supervisor_agent": diagnostics.get("last_multi_agent_orchestration"),
            "worker_agents": ((diagnostics.get("last_multi_agent_orchestration") or {}).get("worker_agent_ids", []) if isinstance(diagnostics.get("last_multi_agent_orchestration"), dict) else []),
            "delegated_tasks": ((diagnostics.get("last_multi_agent_orchestration") or {}).get("delegated_tasks", []) if isinstance(diagnostics.get("last_multi_agent_orchestration"), dict) else []),
            "aggregated_results": ((diagnostics.get("last_multi_agent_orchestration") or {}).get("aggregated_results", []) if isinstance(diagnostics.get("last_multi_agent_orchestration"), dict) else []),
        }

    def get_goal_graph(self, runtime_context: Dict[str, Any]) -> Dict[str, Any]:
        return self.runtime_observatory_engine.build_goal_graph(runtime_context=runtime_context)

    def get_task_graph(self, runtime_context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "nodes": [
                {"id": "tasks", "label": "Tasks", "object": runtime_context.get("active_tasks", [])},
                {"id": "capabilities", "label": "Capabilities", "object": runtime_context.get("capability_scores", {})},
                {"id": "execution_results", "label": "Execution Results", "object": runtime_context.get("execution_results", [])},
                {"id": "reflection", "label": "Reflection", "object": runtime_context.get("reflection_report")},
                {"id": "evaluation", "label": "Evaluation", "object": runtime_context.get("evaluation_report")},
                {"id": "learning", "label": "Learning", "object": runtime_context.get("learning_report")},
                {"id": "adaptive_planning", "label": "Adaptive Planning", "object": runtime_context.get("adaptive_plan")},
                {"id": "optimization", "label": "Optimization", "object": runtime_context.get("runtime_optimization")},
                {"id": "long_term_knowledge", "label": "Long-Term Knowledge", "object": runtime_context.get("long_term_intelligence")},
                {"id": "response", "label": "Response", "object": runtime_context.get("response")},
            ],
            "edges": [
                {"source": "tasks", "target": "capabilities", "relation": "requires"},
                {"source": "capabilities", "target": "execution_results", "relation": "produces"},
                {"source": "execution_results", "target": "reflection", "relation": "feeds"},
                {"source": "reflection", "target": "evaluation", "relation": "feeds"},
                {"source": "evaluation", "target": "learning", "relation": "feeds"},
                {"source": "learning", "target": "adaptive_planning", "relation": "feeds"},
                {"source": "adaptive_planning", "target": "optimization", "relation": "feeds"},
                {"source": "optimization", "target": "long_term_knowledge", "relation": "persists"},
                {"source": "long_term_knowledge", "target": "response", "relation": "informs"},
            ],
        }

    def get_memory_graph(self, runtime_context: Dict[str, Any]) -> Dict[str, Any]:
        return self.runtime_observatory_engine.build_memory_graph(runtime_context=runtime_context)

    def get_provider_graph(self, runtime_context: Dict[str, Any]) -> Dict[str, Any]:
        return self.runtime_observatory_engine.build_provider_graph(runtime_context=runtime_context)

    def get_multi_agent_graph(self, runtime_context: Dict[str, Any]) -> Dict[str, Any]:
        return self.runtime_observatory_engine.build_multi_agent_graph(runtime_context=runtime_context)

    async def search_runtime_observability(
        self,
        *,
        request_id: str | None = None,
        execution_id: str | None = None,
        goal_id: str | None = None,
        task_id: str | None = None,
        runtime_version: str | None = None,
        provider: str | None = None,
        workflow: str | None = None,
        capability: str | None = None,
    ) -> Dict[str, Any]:
        diagnostics = await self.get_diagnostics()
        traces = await self.get_active_traces()
        self._last_diagnostics_cache = diagnostics
        self._last_traces_cache = traces
        runtime_context = self._build_runtime_context(diagnostics=diagnostics, traces=traces)
        return self.runtime_observatory_engine.search(
            runtime_context=runtime_context,
            request_id=request_id,
            execution_id=execution_id,
            goal_id=goal_id,
            task_id=task_id,
            runtime_version=runtime_version,
            provider=provider,
            workflow=workflow,
            capability=capability,
        )
