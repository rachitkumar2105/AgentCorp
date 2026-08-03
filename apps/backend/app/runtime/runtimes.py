"""
Concrete runtime adapters.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from dataclasses import asdict
from datetime import datetime, timezone

from app.models.user import User
from app.schemas.chat import (
    ChatCreateRequest,
    ChatContinueRequest,
    ChatRegenerateRequest,
    ChatRetryRequest,
    ChatResponseSchema,
    ConversationDetailSchema,
)
from app.schemas.streaming import StreamingChatRequest
from app.runtime.cognitive import CognitiveEngine, CognitiveState
from app.runtime.execution import ExecutionContext, create_execution_context, build_lifecycle_entry
from app.runtime.engine import ExecutionEngine
from app.runtime.dispatcher import CapabilityDispatcher
from app.runtime.capabilities import CapabilityRegistry
from app.runtime.evaluation import EvaluationEngine
from app.runtime.autonomous_execution import AutonomousExecutionEngine
from app.runtime.adaptive_planning import AdaptivePlanningEngine
from app.runtime.learning import LearningEngine, LearningPolicy
from app.runtime.reflection import ReflectionEngine
from app.runtime.optimization import OptimizationPolicy, RuntimeOptimizationEngine
from app.runtime.long_term_intelligence import LongTermIntelligenceEngine
from app.runtime.governance import GovernanceEngine
from app.runtime.native_executors import build_native_capability_registry
from app.runtime.planning import ExecutionBlueprint, PlanningEngine
from app.observability.diagnostics import (
    register_adaptive_plan,
    register_execution_context,
    register_execution_engine,
    register_evaluation_report,
    register_learning_policy,
    register_learning_report,
    register_reflection_report,
    register_long_term_intelligence,
    register_runtime_optimization,
    register_runtime_governance,
)
from app.services.chat_service import ChatService
from app.services.knowledge_service import KnowledgeService
from app.services.memory_service import MemoryService
from app.services.provider_service import ProviderService
from app.services.rag_service import RAGService
from app.services.streaming_service import StreamingService
from app.services.tool_execution_service import ToolExecutionService
from app.services.workflow_service import WorkflowService


class V1Runtime:
    def __init__(self, chat_service: ChatService, streaming_service: StreamingService) -> None:
        self.chat_service = chat_service
        self.streaming_service = streaming_service

    async def execute_chat(self, *, payload: ChatCreateRequest | ChatContinueRequest | ChatRegenerateRequest | ChatRetryRequest, current_user: User, organization_id: int, conversation_id: int | None = None) -> ChatResponseSchema | ConversationDetailSchema:
        if isinstance(payload, ChatCreateRequest):
            return self.chat_service.create_chat(payload=payload, current_user=current_user, organization_id=organization_id)
        if isinstance(payload, ChatContinueRequest):
            if conversation_id is None:
                raise ValueError("conversation_id is required for continue chat.")
            return self.chat_service.continue_chat(conversation_id=conversation_id, payload=payload, current_user=current_user, organization_id=organization_id)
        if isinstance(payload, ChatRegenerateRequest):
            if conversation_id is None:
                raise ValueError("conversation_id is required for regenerate chat.")
            return self.chat_service.regenerate_response(conversation_id=conversation_id, payload=payload, current_user=current_user, organization_id=organization_id)
        if isinstance(payload, ChatRetryRequest):
            if conversation_id is None:
                raise ValueError("conversation_id is required for retry chat.")
            return self.chat_service.retry_failed_message(conversation_id=conversation_id, payload=payload, current_user=current_user, organization_id=organization_id)
        raise TypeError(f"Unsupported payload type: {type(payload)!r}")

    async def execute_stream(self, *, payload: StreamingChatRequest, current_user: User, organization_id: int, conversation_id: int | None = None) -> AsyncGenerator[str, None]:
        if conversation_id is None:
            async for event in self.streaming_service.stream_new_chat(payload=payload, current_user=current_user, organization_id=organization_id):
                yield event
            return
        async for event in self.streaming_service.stream_continue_chat(conversation_id=conversation_id, payload=payload, current_user=current_user, organization_id=organization_id):
            yield event

    async def execute_agent(self, *args, **kwargs):
        raise NotImplementedError

    async def execute_workflow(self, *args, **kwargs):
        raise NotImplementedError

    async def execute_tools(self, *args, **kwargs):
        raise NotImplementedError


class V2Runtime(V1Runtime):
    def __init__(
        self,
        chat_service: ChatService,
        streaming_service: StreamingService,
        cognitive_engine: CognitiveEngine | None = None,
        planning_engine: PlanningEngine | None = None,
        memory_service: MemoryService | None = None,
        knowledge_service: KnowledgeService | None = None,
        rag_service: RAGService | None = None,
        workflow_service: WorkflowService | None = None,
        tool_execution_service: ToolExecutionService | None = None,
        provider_service: ProviderService | None = None,
        capability_registry: CapabilityRegistry | None = None,
    ) -> None:
        super().__init__(chat_service=chat_service, streaming_service=streaming_service)
        self.cognitive_engine = cognitive_engine or CognitiveEngine()
        self.planning_engine = planning_engine or PlanningEngine()
        self.memory_service = memory_service
        from app.runtime.adapter import RuntimeV1Adapter
        self.capability_registry = capability_registry or build_native_capability_registry(
            adapter=RuntimeV1Adapter(self),
            memory_service=memory_service,
            knowledge_service=knowledge_service,
            rag_service=rag_service,
            workflow_service=workflow_service,
            tool_execution_service=tool_execution_service,
            provider_service=provider_service,
            streaming_service=streaming_service,
        )
        self.capability_dispatcher = CapabilityDispatcher(RuntimeV1Adapter(self), capability_registry=self.capability_registry)
        self.execution_engine = ExecutionEngine(self.capability_dispatcher)
        self.reflection_engine = ReflectionEngine()
        self.evaluation_engine = EvaluationEngine()
        self.learning_engine = LearningEngine()
        self.learning_policy = LearningPolicy()
        self.adaptive_planning_engine = AdaptivePlanningEngine(self.planning_engine)
        self.long_term_intelligence_engine = LongTermIntelligenceEngine(memory_service=self.memory_service)
        self.runtime_optimization_engine = RuntimeOptimizationEngine()
        self.governance_engine = GovernanceEngine()
        self.autonomous_execution_engine = AutonomousExecutionEngine(self)

    def analyze_request(self, request_text: str, runtime_version: str, request_id: str | None = None) -> CognitiveState:
        return self.cognitive_engine.analyze(
            request_text=request_text,
            runtime_version=runtime_version,
            request_id=request_id,
        )

    def plan_request(self, cognitive_state: CognitiveState, runtime_version: str, request_id: str | None = None) -> ExecutionBlueprint:
        return self.planning_engine.plan(
            cognitive_state=cognitive_state,
            runtime_version=runtime_version,
            request_id=request_id,
        )

    def build_execution_context(self, *, payload: ChatCreateRequest | ChatContinueRequest | ChatRegenerateRequest | ChatRetryRequest | StreamingChatRequest, runtime_version: str, request_id: str | None = None) -> ExecutionContext:
        context = create_execution_context(
            original_request=payload,
            runtime_version=runtime_version,
            request_id=request_id,
        )
        cognitive_state = self.analyze_request(
            request_text=payload.message,
            runtime_version=runtime_version,
            request_id=request_id,
        )
        execution_blueprint = self.plan_request(
            cognitive_state=cognitive_state,
            runtime_version=runtime_version,
            request_id=request_id,
        )
        now = context.execution_metadata.created_at if context.execution_metadata else None
        lifecycle = (
            build_lifecycle_entry(
                stage_name="Request Received",
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
                status="COMPLETED",
                summary="Request accepted.",
                request_id=context.execution_metadata.request_id if context.execution_metadata else None,
                trace_id=context.execution_metadata.trace_id if context.execution_metadata else None,
                runtime_version=runtime_version,
            ),
        )
        return context.with_updates(
            cognitive_state=cognitive_state,
            execution_blueprint=execution_blueprint,
            runtime_capabilities=cognitive_state.required_runtime_capabilities,
            observability_references=("runtime_observatory",),
            execution_state="READY",
            execution_trace=lifecycle,
            execution_timestamps=(now,) if now else (),
        )

    async def enforce_governance(self, *, payload: ChatCreateRequest | ChatContinueRequest | ChatRegenerateRequest | ChatRetryRequest | StreamingChatRequest, current_user: User, organization_id: int, runtime_version: str):
        organization = type("OrganizationContext", (), {"id": organization_id, "is_active": True, "requires_approval": False})()
        report = await self.governance_engine.govern(
            payload=payload,
            user=current_user,
            organization=organization,
            affected_runtime=runtime_version,
        )
        if not report.decision.allowed:
            from app.security.exceptions import PolicyViolationError
            raise PolicyViolationError(report.decision.reason)
        return report

    async def execute_chat(self, *, payload: ChatCreateRequest | ChatContinueRequest | ChatRegenerateRequest | ChatRetryRequest, current_user: User, organization_id: int, conversation_id: int | None = None) -> ChatResponseSchema | ConversationDetailSchema:
        runtime_version = getattr(payload, "runtime_version", "AgentCorp V1")
        governance_report = None
        if runtime_version == "AgentCorp V2":
            governance_report = await self.enforce_governance(
                payload=payload,
                current_user=current_user,
                organization_id=organization_id,
                runtime_version=runtime_version,
            )
        execution_context = self.build_execution_context(payload=payload, runtime_version=runtime_version)
        if governance_report is not None:
            governance_trace = tuple(
                build_lifecycle_entry(
                    stage_name=entry["stage_name"],
                    started_at=datetime.now(timezone.utc),
                    completed_at=datetime.now(timezone.utc),
                    status=entry["status"],
                    summary=entry["summary"],
                    confidence=governance_report.decision.allowed and 1.0 or 0.0,
                    request_id=execution_context.execution_metadata.request_id if execution_context.execution_metadata else None,
                    trace_id=execution_context.execution_metadata.trace_id if execution_context.execution_metadata else None,
                    runtime_version=execution_context.runtime_version,
                    output_snapshot=entry,
                )
                for entry in governance_report.trace
            )
            execution_context = execution_context.with_updates(
                execution_trace=governance_trace + execution_context.execution_trace,
            )
        if execution_context.execution_metadata is not None:
            await register_execution_context(
                execution_context.execution_metadata.execution_id,
                {
                    "execution_context": {
                        "runtime_version": execution_context.runtime_version,
                        "execution_metadata": execution_context.execution_metadata.__dict__,
                        "runtime_capabilities": execution_context.runtime_capabilities,
                        "observability_references": execution_context.observability_references,
                        "execution_state": execution_context.execution_state,
                        "execution_trace": [entry.__dict__ for entry in execution_context.execution_trace],
                    }
                },
            )
        response = await self.execution_engine.execute_chat(
            execution_context=execution_context,
            payload=payload,
            current_user=current_user,
            organization_id=organization_id,
            conversation_id=conversation_id,
        )
        await self._record_analysis(
            execution_context=execution_context,
            response=response,
            current_user=current_user,
            organization_id=organization_id,
        )
        return response

    async def execute_stream(self, *, payload: StreamingChatRequest, current_user: User, organization_id: int, conversation_id: int | None = None) -> AsyncGenerator[str, None]:
        runtime_version = getattr(payload, "runtime_version", "AgentCorp V1")
        governance_report = None
        if runtime_version == "AgentCorp V2":
            governance_report = await self.enforce_governance(
                payload=payload,
                current_user=current_user,
                organization_id=organization_id,
                runtime_version=runtime_version,
            )
        execution_context = self.build_execution_context(payload=payload, runtime_version=runtime_version)
        if governance_report is not None:
            governance_trace = tuple(
                build_lifecycle_entry(
                    stage_name=entry["stage_name"],
                    started_at=datetime.now(timezone.utc),
                    completed_at=datetime.now(timezone.utc),
                    status=entry["status"],
                    summary=entry["summary"],
                    confidence=governance_report.decision.allowed and 1.0 or 0.0,
                    request_id=execution_context.execution_metadata.request_id if execution_context.execution_metadata else None,
                    trace_id=execution_context.execution_metadata.trace_id if execution_context.execution_metadata else None,
                    runtime_version=execution_context.runtime_version,
                    output_snapshot=entry,
                )
                for entry in governance_report.trace
            )
            execution_context = execution_context.with_updates(
                execution_trace=governance_trace + execution_context.execution_trace,
            )
        if execution_context.execution_metadata is not None:
            await register_execution_context(
                execution_context.execution_metadata.execution_id,
                {
                    "execution_context": {
                        "runtime_version": execution_context.runtime_version,
                        "execution_metadata": execution_context.execution_metadata.__dict__,
                        "runtime_capabilities": execution_context.runtime_capabilities,
                        "observability_references": execution_context.observability_references,
                        "execution_state": execution_context.execution_state,
                        "execution_trace": [entry.__dict__ for entry in execution_context.execution_trace],
                    }
                },
            )
        async for event in self.execution_engine.execute_stream(
            execution_context=execution_context,
            payload=payload,
            current_user=current_user,
            organization_id=organization_id,
            conversation_id=conversation_id,
        ):
            yield event

    async def execute_autonomous_goal(self, *, goal, current_user: User, organization_id: int):
        return await self.autonomous_execution_engine.execute_goal(
            goal=goal,
            current_user=current_user,
            organization_id=organization_id,
        )

    async def _record_analysis(
        self,
        *,
        execution_context: ExecutionContext,
        response: ChatResponseSchema | ConversationDetailSchema,
        current_user: User,
        organization_id: int,
    ) -> None:
        if execution_context.execution_metadata is None or execution_context.execution_blueprint is None:
            return
        diagnostics_payload = response.model_dump() if hasattr(response, "model_dump") else response
        execution_result = self._build_execution_result(execution_context=execution_context, response_payload=diagnostics_payload)
        reflection_started = datetime.now(timezone.utc)
        reflection_report = self.reflection_engine.reflect(
            execution_context=execution_context,
            execution_result=execution_result,
            execution_trace=execution_context.execution_trace,
        )
        reflection_completed = datetime.now(timezone.utc)
        evaluation_started = datetime.now(timezone.utc)
        evaluation_report = self.evaluation_engine.evaluate(
            execution_context=execution_context,
            execution_result=execution_result,
            reflection_report=reflection_report,
        )
        evaluation_completed = datetime.now(timezone.utc)
        evaluation_trace = execution_context.execution_trace + (
            build_lifecycle_entry(
                stage_name="Reflection Started",
                started_at=reflection_started,
                completed_at=reflection_started,
                status="COMPLETED",
                summary="Reflection analysis started.",
                confidence=reflection_report.confidence,
                request_id=execution_context.execution_metadata.request_id,
                trace_id=execution_context.execution_metadata.trace_id,
                runtime_version=execution_context.runtime_version,
            ),
            build_lifecycle_entry(
                stage_name="Reflection Completed",
                started_at=reflection_started,
                completed_at=reflection_completed,
                status="COMPLETED",
                summary=reflection_report.execution_summary,
                confidence=reflection_report.confidence,
                request_id=execution_context.execution_metadata.request_id,
                trace_id=execution_context.execution_metadata.trace_id,
                runtime_version=execution_context.runtime_version,
                output_snapshot=asdict(reflection_report),
                warnings=reflection_report.warnings,
            ),
            build_lifecycle_entry(
                stage_name="Evaluation Started",
                started_at=evaluation_started,
                completed_at=evaluation_started,
                status="COMPLETED",
                summary="Evaluation analysis started.",
                confidence=evaluation_report.confidence,
                request_id=execution_context.execution_metadata.request_id,
                trace_id=execution_context.execution_metadata.trace_id,
                runtime_version=execution_context.runtime_version,
            ),
            build_lifecycle_entry(
                stage_name="Evaluation Completed",
                started_at=evaluation_started,
                completed_at=evaluation_completed,
                status="COMPLETED",
                summary=evaluation_report.evaluation_summary,
                confidence=evaluation_report.confidence,
                request_id=execution_context.execution_metadata.request_id,
                trace_id=execution_context.execution_metadata.trace_id,
                runtime_version=execution_context.runtime_version,
                output_snapshot=asdict(evaluation_report),
            ),
        )
        learning_started = datetime.now(timezone.utc)
        learning_report = self.learning_engine.learn(
            execution_context=execution_context,
            reflection_report=reflection_report,
            evaluation_report=evaluation_report,
            execution_trace=evaluation_trace,
        )
        policy_decision = self.learning_policy.decide(learning_report)
        learning_completed = datetime.now(timezone.utc)
        learning_trace = evaluation_trace + (
            build_lifecycle_entry(
                stage_name="Learning Started",
                started_at=learning_started,
                completed_at=learning_started,
                status="COMPLETED",
                summary="Learning analysis started.",
                confidence=learning_report.confidence,
                request_id=execution_context.execution_metadata.request_id,
                trace_id=execution_context.execution_metadata.trace_id,
                runtime_version=execution_context.runtime_version,
            ),
            build_lifecycle_entry(
                stage_name="Learning Analysis",
                started_at=learning_started,
                completed_at=learning_completed,
                status="COMPLETED",
                summary=learning_report.summary,
                confidence=learning_report.confidence,
                request_id=execution_context.execution_metadata.request_id,
                trace_id=execution_context.execution_metadata.trace_id,
                runtime_version=execution_context.runtime_version,
                output_snapshot={
                    "reusable_observations": [item.__dict__ for item in learning_report.reusable_observations],
                    "reusable_preferences": [item.__dict__ for item in learning_report.reusable_preferences],
                    "reusable_execution_patterns": [item.__dict__ for item in learning_report.reusable_execution_patterns],
                    "reusable_capability_patterns": [item.__dict__ for item in learning_report.reusable_capability_patterns],
                    "reusable_workflow_patterns": [item.__dict__ for item in learning_report.reusable_workflow_patterns],
                },
            ),
            build_lifecycle_entry(
                stage_name="Learning Policy",
                started_at=learning_completed,
                completed_at=learning_completed,
                status="COMPLETED",
                summary=policy_decision.reason,
                confidence=learning_report.confidence,
                request_id=execution_context.execution_metadata.request_id,
                trace_id=execution_context.execution_metadata.trace_id,
                runtime_version=execution_context.runtime_version,
                output_snapshot={
                    "decision": policy_decision.decision.value,
                    "persist_memory": policy_decision.persist_memory,
                    "memory_type": policy_decision.memory_type,
                    "importance_score": policy_decision.importance_score,
                },
            ),
        )
        if policy_decision.persist_memory and self.memory_service is not None:
            self._persist_learning(
                execution_context=execution_context,
                learning_report=learning_report,
                policy_decision=policy_decision,
                current_user=current_user,
                organization_id=organization_id,
            )
        learning_completed_trace = learning_trace + (
            build_lifecycle_entry(
                stage_name="Learning Completed",
                started_at=learning_completed,
                completed_at=learning_completed,
                status="COMPLETED",
                summary="Learning analysis completed.",
                confidence=learning_report.confidence,
                request_id=execution_context.execution_metadata.request_id,
                trace_id=execution_context.execution_metadata.trace_id,
                runtime_version=execution_context.runtime_version,
            ),
        )
        adaptive_report = self.adaptive_planning_engine.revise_blueprint(
            goal=execution_context.execution_blueprint,
            previous_blueprint=execution_context.execution_blueprint,
            reflection_report=reflection_report,
            evaluation_report=evaluation_report,
            learning_report=learning_report,
        )
        await register_adaptive_plan(
            execution_context.execution_metadata.execution_id,
            {
                "goal_id": getattr(adaptive_report.goal, "goal_id", None),
                "replanning_required": adaptive_report.replanning_required,
                "replanning_reason": adaptive_report.replanning_reason,
                "revision_number": adaptive_report.revision_number,
                "planning_confidence": adaptive_report.planning_confidence,
                "tasks_added": [task.identifier for task in adaptive_report.plan_diff.added_tasks],
                "tasks_removed": [task.identifier for task in adaptive_report.plan_diff.removed_tasks],
                "tasks_preserved": [task.identifier for task in adaptive_report.revised_blueprint.task_graph if task.identifier not in {removed.identifier for removed in adaptive_report.plan_diff.removed_tasks}],
            },
        )
        long_term_report = await self.long_term_intelligence_engine.persist_intelligence(
            organization_id=organization_id,
            agent_id=1,
            current_user=current_user,
            learning_report=learning_report,
            adaptive_report=adaptive_report,
        )
        long_term_trace = learning_completed_trace + tuple(
            build_lifecycle_entry(
                stage_name=entry["stage_name"],
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
                status=entry["status"],
                summary=entry["summary"],
                confidence=long_term_report.intelligence_confidence,
                request_id=execution_context.execution_metadata.request_id,
                trace_id=execution_context.execution_metadata.trace_id,
                runtime_version=execution_context.runtime_version,
                output_snapshot=entry,
            )
            for entry in long_term_report.trace
        )
        runtime_optimization_started = datetime.now(timezone.utc)
        runtime_optimization_report = self.runtime_optimization_engine.optimize(
            long_term_report=long_term_report,
            optimization_policy=OptimizationPolicy.BALANCED,
            capability_scores=long_term_report.capability_scores,
        )
        optimization_trace = long_term_trace + tuple(
            build_lifecycle_entry(
                stage_name=entry["stage_name"],
                started_at=runtime_optimization_started,
                completed_at=datetime.now(timezone.utc),
                status=entry["status"],
                summary=entry["summary"],
                confidence=runtime_optimization_report.estimated_improvement,
                request_id=execution_context.execution_metadata.request_id,
                trace_id=execution_context.execution_metadata.trace_id,
                runtime_version=execution_context.runtime_version,
                output_snapshot=entry,
            )
            for entry in runtime_optimization_report.trace
        )
        await register_runtime_optimization(
            execution_context.execution_metadata.execution_id,
            {
                "policy": runtime_optimization_report.policy.value,
                "provider_recommendation": runtime_optimization_report.provider_recommendation.__dict__,
                "workflow_recommendation": runtime_optimization_report.workflow_recommendation.__dict__,
                "tool_recommendation": runtime_optimization_report.tool_recommendation.__dict__,
                "capability_recommendation": runtime_optimization_report.capability_recommendation.__dict__,
                "prompt_recommendation": runtime_optimization_report.prompt_recommendation.__dict__,
                "execution_ordering": list(runtime_optimization_report.execution_ordering),
                "estimated_improvement": runtime_optimization_report.estimated_improvement,
                "trace": [entry for entry in runtime_optimization_report.trace],
                "persisted": runtime_optimization_report.persisted,
            },
        )
        await register_long_term_intelligence(
            execution_context.execution_metadata.execution_id,
            {
                "intelligence_confidence": long_term_report.intelligence_confidence,
                "consolidated_memories": list(long_term_report.consolidated_memories),
                "forgotten_memories": list(long_term_report.forgotten_memories),
                "evolved_preferences": list(long_term_report.evolved_preferences),
                "discovered_patterns": list(long_term_report.discovered_patterns),
                "capability_scores": long_term_report.capability_scores,
                "persisted": long_term_report.persisted,
                "trace": list(long_term_report.trace),
            },
        )
        await register_learning_report(
            execution_context.execution_metadata.execution_id,
            {
                "learning_report": {
                    "summary": learning_report.summary,
                    "confidence": learning_report.confidence,
                    "learning_priority": learning_report.learning_priority,
                    "persistence_recommendation": learning_report.persistence_recommendation.value,
                    "reusable_observations": [item.__dict__ for item in learning_report.reusable_observations],
                    "reusable_preferences": [item.__dict__ for item in learning_report.reusable_preferences],
                    "reusable_execution_patterns": [item.__dict__ for item in learning_report.reusable_execution_patterns],
                    "reusable_capability_patterns": [item.__dict__ for item in learning_report.reusable_capability_patterns],
                    "reusable_workflow_patterns": [item.__dict__ for item in learning_report.reusable_workflow_patterns],
                }
            },
        )
        await register_learning_policy(
            execution_context.execution_metadata.execution_id,
            {
                "decision": policy_decision.decision.value,
                "reason": policy_decision.reason,
                "persist_memory": policy_decision.persist_memory,
                "memory_type": policy_decision.memory_type,
                "importance_score": policy_decision.importance_score,
            },
        )
        await register_execution_context(
            execution_context.execution_metadata.execution_id,
            {
                "execution_context": {
                    "runtime_version": execution_context.runtime_version,
                    "execution_metadata": execution_context.execution_metadata.__dict__,
                    "runtime_capabilities": execution_context.runtime_capabilities,
                    "observability_references": execution_context.observability_references,
                    "execution_state": execution_context.execution_state,
                    "execution_trace": [entry.__dict__ for entry in optimization_trace],
                },
                "reflection_report": asdict(reflection_report),
                "evaluation_report": asdict(evaluation_report),
                "learning_report": {
                    "summary": learning_report.summary,
                    "confidence": learning_report.confidence,
                    "learning_priority": learning_report.learning_priority,
                    "persistence_recommendation": learning_report.persistence_recommendation.value,
                },
                "learning_policy": {
                    "decision": policy_decision.decision.value,
                    "reason": policy_decision.reason,
                    "persist_memory": policy_decision.persist_memory,
                },
                "long_term_intelligence": {
                    "intelligence_confidence": long_term_report.intelligence_confidence,
                    "persisted": long_term_report.persisted,
                },
            },
        )
        await register_execution_engine(
            execution_context.execution_metadata.execution_id,
            {
                "execution_initialized": True,
                "execution_state": "COMPLETED",
                "current_task": execution_context.execution_trace[-1].__dict__ if execution_context.execution_trace else None,
                "completed_tasks": [],
                "pending_tasks": [],
                "execution_timeline": [entry.__dict__ for entry in optimization_trace],
                "execution_results": [asdict(execution_result)],
                "state_transitions": [],
                "execution_trace": [entry.__dict__ for entry in optimization_trace],
                "learning_report": {
                    "summary": learning_report.summary,
                    "confidence": learning_report.confidence,
                    "learning_priority": learning_report.learning_priority,
                    "persistence_recommendation": learning_report.persistence_recommendation.value,
                },
                "learning_policy": {
                    "decision": policy_decision.decision.value,
                    "reason": policy_decision.reason,
                    "persist_memory": policy_decision.persist_memory,
                },
                "long_term_intelligence": {
                    "intelligence_confidence": long_term_report.intelligence_confidence,
                    "persisted": long_term_report.persisted,
                },
            },
        )
        await register_reflection_report(execution_context.execution_metadata.execution_id, asdict(reflection_report))
        await register_evaluation_report(execution_context.execution_metadata.execution_id, asdict(evaluation_report))
        await register_execution_context(
            f"{execution_context.execution_metadata.execution_id}:analysis",
            {
                "execution_trace": [entry.__dict__ for entry in optimization_trace],
                "reflection_report": asdict(reflection_report),
                "evaluation_report": asdict(evaluation_report),
                "learning_report": {
                    "summary": learning_report.summary,
                    "confidence": learning_report.confidence,
                    "learning_priority": learning_report.learning_priority,
                    "persistence_recommendation": learning_report.persistence_recommendation.value,
                },
                "learning_policy": {
                    "decision": policy_decision.decision.value,
                    "reason": policy_decision.reason,
                    "persist_memory": policy_decision.persist_memory,
                },
                "long_term_intelligence": {
                    "intelligence_confidence": long_term_report.intelligence_confidence,
                    "persisted": long_term_report.persisted,
                },
                "runtime_optimization": {
                    "policy": runtime_optimization_report.policy.value,
                    "estimated_improvement": runtime_optimization_report.estimated_improvement,
                    "provider_recommendation": runtime_optimization_report.provider_recommendation.__dict__,
                    "workflow_recommendation": runtime_optimization_report.workflow_recommendation.__dict__,
                    "tool_recommendation": runtime_optimization_report.tool_recommendation.__dict__,
                    "capability_recommendation": runtime_optimization_report.capability_recommendation.__dict__,
                    "prompt_recommendation": runtime_optimization_report.prompt_recommendation.__dict__,
                    "execution_ordering": list(runtime_optimization_report.execution_ordering),
                },
            },
        )

    def _persist_learning(self, *, execution_context: ExecutionContext, learning_report, policy_decision, current_user: User, organization_id: int) -> None:
        if self.memory_service is None or execution_context.execution_metadata is None:
            return
        content = {
            "summary": learning_report.summary,
            "confidence": learning_report.confidence,
            "learning_priority": learning_report.learning_priority,
            "persistence_recommendation": learning_report.persistence_recommendation.value,
            "reusable_observations": [item.__dict__ for item in learning_report.reusable_observations],
            "reusable_preferences": [item.__dict__ for item in learning_report.reusable_preferences],
            "reusable_execution_patterns": [item.__dict__ for item in learning_report.reusable_execution_patterns],
            "reusable_capability_patterns": [item.__dict__ for item in learning_report.reusable_capability_patterns],
            "reusable_workflow_patterns": [item.__dict__ for item in learning_report.reusable_workflow_patterns],
        }
        self.memory_service.create_memory(
            org_id=organization_id,
            agent_id=1,
            title=f"Learning: {learning_report.metadata.execution_id or execution_context.execution_metadata.execution_id}",
            content=str(content),
            memory_type=policy_decision.memory_type or "episodic",
            importance_score=policy_decision.importance_score,
            confidence_score=learning_report.confidence,
            user_id=getattr(current_user, "id", 1),
        )

    def _build_execution_result(self, *, execution_context: ExecutionContext, response_payload: object):
        from app.runtime.execution import ExecutionResult, ExecutionState

        return ExecutionResult(
            task_id="provider",
            status=ExecutionState.COMPLETED,
            outputs={"response": response_payload},
            errors=(),
            duration=0.0,
            metadata={
                "required_capability": "provider",
                "source": "runtime_analysis",
            },
            started_at=execution_context.execution_metadata.created_at if execution_context.execution_metadata else "",
            completed_at=execution_context.execution_metadata.created_at if execution_context.execution_metadata else "",
        )
