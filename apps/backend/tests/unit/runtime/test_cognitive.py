from __future__ import annotations

from dataclasses import asdict

from app.runtime.cognitive import (
    CognitiveEngine,
    GoalUnderstandingAnalyzer,
    IntentAnalyzer,
    ConstraintAnalyzer,
    CapabilityAnalyzer,
    ComplexityAnalyzer,
    CognitiveState,
)
from app.runtime.capabilities import CapabilityMetadata, CapabilityRegistry, CapabilityExecutionMode
from app.runtime.dispatcher import CapabilityDispatcher
from app.runtime.engine import ExecutionEngine
from app.runtime.execution import (
    ExecutionResult,
    ExecutionState,
    ExecutionStateMachine,
    ExecutionTask,
    build_execution_tasks,
    create_execution_context,
)
from app.runtime.evaluation import EvaluationEngine
from app.runtime.learning import LearningDecision, LearningEngine, LearningPolicy, LearningReport, LearningReportMetadata, LearningArtifact, LearningPolicyDecision
from app.runtime.native_executors import build_native_capability_registry
from app.runtime.reflection import ReflectionEngine
from app.runtime.planning import PlanningEngine
from app.runtime.runtimes import V2Runtime, V1Runtime
from app.runtime.router import RuntimeRouter, RuntimeVersion
from app.services.observability_service import ObservabilityService


def test_goal_understanding_analyzer_normalizes_text() -> None:
    state = CognitiveState(raw_request="Please implement a frontend runtime selector for V2.")
    updated = GoalUnderstandingAnalyzer().analyze(state)
    assert "frontend runtime selector" in updated.normalized_goal


def test_intent_analyzer_detects_multiple_intents() -> None:
    state = CognitiveState(raw_request="Research and write code for workflow automation.")
    updated = IntentAnalyzer().analyze(state)
    categories = {intent.category for intent in updated.intent_collection}
    assert "research" in categories
    assert "coding" in categories
    assert "automation" in categories


def test_constraint_analyzer_records_unknown_when_absent() -> None:
    state = CognitiveState(raw_request="Build something useful.")
    updated = ConstraintAnalyzer().analyze(state)
    assert "unknown" in updated.constraint_collection


def test_capability_analyzer_maps_runtime_needs() -> None:
    state = CognitiveState(raw_request="Need memory, RAG, workflow, and streaming support.")
    updated = CapabilityAnalyzer().analyze(state)
    assert set(updated.required_runtime_capabilities) >= {"Memory", "RAG", "Workflow", "Streaming"}


def test_complexity_analyzer_produces_structured_assessment() -> None:
    state = CognitiveState(raw_request="Phase 1A architecture integration for backend and frontend observability.")
    updated = ComplexityAnalyzer().analyze(state)
    assert updated.complexity_assessment is not None
    assert updated.complexity_assessment.reasoning_complexity in {"high", "medium", "low"}


def test_cognitive_engine_builds_trace_and_metadata() -> None:
    engine = CognitiveEngine()
    state = engine.analyze(
        request_text="Please implement a workflow and explain the architecture.",
        runtime_version=RuntimeVersion.V2.value,
        request_id="req-123",
    )
    assert state.processing_metadata is not None
    assert state.processing_metadata.runtime_version == RuntimeVersion.V2.value
    assert state.processing_metadata.request_id == "req-123"
    assert len(state.analysis_trace) == 5


def test_planning_engine_builds_structured_blueprint() -> None:
    cognitive_state = CognitiveEngine().analyze(
        request_text="Please implement a backend architecture plan with observability and workflow support.",
        runtime_version=RuntimeVersion.V2.value,
        request_id="req-456",
    )
    blueprint = PlanningEngine().plan(
        cognitive_state=cognitive_state,
        runtime_version=RuntimeVersion.V2.value,
        request_id="req-456",
    )
    assert blueprint.planning_metadata is not None
    assert blueprint.execution_objective is not None
    assert len(blueprint.task_graph) == 3
    assert len(blueprint.dependency_graph) >= 1
    assert len(blueprint.milestones) == 1
    assert blueprint.planning_trace[-1].stage_name == "Blueprint Assembly"


def test_v2_runtime_runs_cognitive_analysis_before_delegating() -> None:
    class DummyChat:
        def create_chat(self, **kwargs):
            return {"ok": True}

    class DummyStream:
        async def stream_new_chat(self, **kwargs):
            if False:
                yield ""

        async def stream_continue_chat(self, **kwargs):
            if False:
                yield ""

    class DummyProviderService:
        async def chat(self, *args, **kwargs):
            class Result:
                def model_dump(self):
                    return {"provider": True}

            return Result()

        async def list_models(self, *args, **kwargs):
            return ["model-a"]

    runtime = V2Runtime(chat_service=DummyChat(), streaming_service=DummyStream(), provider_service=DummyProviderService())
    state = runtime.analyze_request("Please summarize the request and explain the constraints.", RuntimeVersion.V2.value)
    assert state.normalized_goal is not None
    assert state.analysis_trace[0].stage_name == "Goal Understanding"
    blueprint = runtime.plan_request(state, RuntimeVersion.V2.value)
    assert blueprint.execution_objective is not None
    assert blueprint.planning_trace[0].stage_name == "Objective Planning"


def test_reflection_engine_produces_structured_report() -> None:
    cognitive_state = CognitiveEngine().analyze(
        request_text="Please implement a runtime execution engine.",
        runtime_version=RuntimeVersion.V2.value,
        request_id="req-reflect",
    )
    blueprint = PlanningEngine().plan(
        cognitive_state=cognitive_state,
        runtime_version=RuntimeVersion.V2.value,
        request_id="req-reflect",
    )
    context = create_execution_context(
        original_request={"message": "Please implement a runtime execution engine."},
        runtime_version=RuntimeVersion.V2.value,
        request_id="req-reflect",
    ).with_updates(cognitive_state=cognitive_state, execution_blueprint=blueprint)
    execution_result = ExecutionResult(
        task_id="capability_provider",
        status=ExecutionState.COMPLETED,
        outputs={"response": {"ok": True}},
        errors=(),
        duration=0.01,
        metadata={"required_capability": "provider"},
        started_at="2026-08-02T00:00:00+00:00",
        completed_at="2026-08-02T00:00:00+00:00",
    )
    report = ReflectionEngine().reflect(
        execution_context=context,
        execution_result=execution_result,
        execution_trace=context.execution_trace,
    )
    assert report.execution_summary
    assert report.observations
    assert report.metadata.execution_id == "req-reflect" or report.metadata.execution_id is not None
    assert report.confidence > 0


def test_evaluation_engine_produces_structured_report() -> None:
    cognitive_state = CognitiveEngine().analyze(
        request_text="Please implement a runtime execution engine.",
        runtime_version=RuntimeVersion.V2.value,
        request_id="req-evaluate",
    )
    blueprint = PlanningEngine().plan(
        cognitive_state=cognitive_state,
        runtime_version=RuntimeVersion.V2.value,
        request_id="req-evaluate",
    )
    context = create_execution_context(
        original_request={"message": "Please implement a runtime execution engine."},
        runtime_version=RuntimeVersion.V2.value,
        request_id="req-evaluate",
    ).with_updates(cognitive_state=cognitive_state, execution_blueprint=blueprint)
    execution_result = ExecutionResult(
        task_id="capability_provider",
        status=ExecutionState.COMPLETED,
        outputs={"response": {"ok": True}},
        errors=(),
        duration=0.01,
        metadata={"required_capability": "provider"},
        started_at="2026-08-02T00:00:00+00:00",
        completed_at="2026-08-02T00:00:00+00:00",
    )
    reflection_report = ReflectionEngine().reflect(
        execution_context=context,
        execution_result=execution_result,
        execution_trace=context.execution_trace,
    )
    report = EvaluationEngine().evaluate(
        execution_context=context,
        execution_result=execution_result,
        reflection_report=reflection_report,
    )
    assert report.quality_score >= 0
    assert report.scores[-1].name == "quality"
    assert report.capability_utilization == ("provider",)


def test_v2_runtime_appends_reflection_and_evaluation_analysis() -> None:
    class DummyChat:
        def create_chat(self, **kwargs):
            return {"ok": True}

    class DummyStream:
        async def stream_new_chat(self, **kwargs):
            if False:
                yield ""

        async def stream_continue_chat(self, **kwargs):
            if False:
                yield ""

    class DummyProviderService:
        async def chat(self, *args, **kwargs):
            class Result:
                def model_dump(self):
                    return {"provider": True}

            return Result()

        async def list_models(self, *args, **kwargs):
            return ["model-a"]

    runtime = V2Runtime(
        chat_service=DummyChat(),
        streaming_service=DummyStream(),
        provider_service=DummyProviderService(),
    )
    payload = type("Payload", (), {"message": "Please implement a runtime execution engine.", "runtime_version": RuntimeVersion.V2.value})()

    import asyncio

    response = asyncio.run(runtime.execute_chat(payload=payload, current_user=object(), organization_id=1))
    assert response == ["model-a"]
    diagnostics = asyncio.run(ObservabilityService.__new__(ObservabilityService).get_diagnostics())
    assert diagnostics["last_reflection_report"]["execution_summary"]
    assert diagnostics["last_evaluation_report"]["evaluation_summary"]
    assert diagnostics["last_execution_engine"]["execution_trace"][-1]["stage_name"] == "Long-Term Intelligence Completed"
    assert diagnostics["last_execution_engine"]["execution_trace"][-2]["stage_name"] == "Long-Term Intelligence Started"
    assert diagnostics["last_execution_engine"]["execution_trace"][-2]["status"] == "SKIPPED"


def test_learning_engine_extracts_preferences_and_experience() -> None:
    cognitive_state = CognitiveEngine().analyze(
        request_text="Please provide a concise, structured workflow for the backend runtime.",
        runtime_version=RuntimeVersion.V2.value,
        request_id="req-learn",
    )
    blueprint = PlanningEngine().plan(
        cognitive_state=cognitive_state,
        runtime_version=RuntimeVersion.V2.value,
        request_id="req-learn",
    )
    context = create_execution_context(
        original_request={"message": "Please provide a concise, structured workflow for the backend runtime."},
        runtime_version=RuntimeVersion.V2.value,
        request_id="req-learn",
    ).with_updates(cognitive_state=cognitive_state, execution_blueprint=blueprint)
    execution_result = ExecutionResult(
        task_id="capability_provider",
        status=ExecutionState.COMPLETED,
        outputs={"response": {"ok": True}},
        errors=(),
        duration=0.01,
        metadata={"required_capability": "provider"},
        started_at="2026-08-02T00:00:00+00:00",
        completed_at="2026-08-02T00:00:00+00:00",
    )
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
    report = LearningEngine().learn(
        execution_context=context,
        reflection_report=reflection_report,
        evaluation_report=evaluation_report,
        execution_trace=context.execution_trace,
    )
    assert report.metadata.execution_id == "req-learn" or report.metadata.execution_id is not None
    assert report.reusable_preferences
    assert any(item.title == "communication" for item in report.reusable_preferences)
    assert any(item.title == "formatting" for item in report.reusable_preferences)
    assert report.reusable_execution_patterns
    assert report.reusable_capability_patterns
    assert report.learning_priority >= 1
    assert report.summary.startswith("Learned ")


def test_learning_policy_is_deterministic_and_blocks_low_confidence() -> None:
    report = LearningReport(
        reusable_observations=(),
        reusable_preferences=(),
        reusable_execution_patterns=(),
        reusable_capability_patterns=(),
        reusable_workflow_patterns=(),
        confidence=0.2,
        learning_priority=1,
        persistence_recommendation=LearningDecision.PERSIST,
        metadata=LearningReportMetadata(
            runtime_version=RuntimeVersion.V2.value,
            execution_id="exec-low",
            request_id="req-low",
            trace_id="trace-low",
            created_at="2026-08-02T00:00:00+00:00",
        ),
        started_at="2026-08-02T00:00:00+00:00",
        completed_at="2026-08-02T00:00:00+00:00",
        duration=0.0,
        summary="Low confidence",
    )
    policy = LearningPolicy()
    decision = policy.decide(report)
    assert decision.decision == LearningDecision.IGNORE
    assert decision.persist_memory is False
    assert policy.decide(report) == decision


def test_v2_runtime_records_learning_observability_and_memory_persistence() -> None:
    class DummyChat:
        def create_chat(self, **kwargs):
            return {"ok": True}

    class DummyStream:
        async def stream_new_chat(self, **kwargs):
            if False:
                yield ""

        async def stream_continue_chat(self, **kwargs):
            if False:
                yield ""

    class DummyProviderService:
        async def chat(self, *args, **kwargs):
            class Result:
                def model_dump(self):
                    return {"provider": True}

            return Result()

        async def list_models(self, *args, **kwargs):
            return ["model-a"]

    class DummyMemoryService:
        def __init__(self):
            self.created = []

        def list_memories(self, org_id, agent_id, memory_type=None):
            return [
                {
                    "title": "User preference",
                    "content": "Prefer concise responses.",
                    "importance_score": 0.6,
                    "confidence_score": 0.7,
                    "memory_type": "semantic",
                    "created_at": None,
                    "updated_at": None,
                    "source": "extraction",
                }
            ]

        def create_memory(self, **kwargs):
            self.created.append(kwargs)
            return kwargs

    runtime = V2Runtime(
        chat_service=DummyChat(),
        streaming_service=DummyStream(),
        provider_service=DummyProviderService(),
        memory_service=DummyMemoryService(),
    )
    payload = type("Payload", (), {"message": "Please provide a concise, structured workflow for the backend runtime.", "runtime_version": RuntimeVersion.V2.value})()

    import asyncio

    response = asyncio.run(runtime.execute_chat(payload=payload, current_user=type("User", (), {"id": 7})(), organization_id=1))
    assert response == ["model-a"]
    diagnostics = asyncio.run(ObservabilityService.__new__(ObservabilityService).get_diagnostics())
    assert diagnostics["last_learning_report"]["learning_report"]["summary"].startswith("Learned ")
    assert diagnostics["last_learning_policy"]["persist_memory"] is True
    assert diagnostics["last_execution_engine"]["execution_trace"][-1]["stage_name"] == "Long-Term Intelligence Completed"
    assert diagnostics["last_execution_engine"]["execution_trace"][-2]["stage_name"] == "Intelligence Persisted"
    assert diagnostics["last_execution_engine"]["execution_trace"][-3]["stage_name"] == "Capability Scoring"
    assert diagnostics["last_execution_engine"]["execution_trace"][-4]["stage_name"] == "Pattern Discovery"


def test_runtime_router_defaults_to_v1() -> None:
    class DummyRuntime(V1Runtime):
        def __init__(self):
            pass

    v1 = object()
    v2 = object()
    router = RuntimeRouter(v1_runtime=v1, v2_runtime=v2)  # type: ignore[arg-type]
    assert router.resolve(None) is v1
    assert router.resolve(RuntimeVersion.V2.value) is v2


def test_runtime_observatory_includes_blueprint_snapshot() -> None:
    service = ObservabilityService.__new__(ObservabilityService)
    snapshot = {
        "last_execution_blueprint": {"planning_metadata": {"runtime_version": RuntimeVersion.V2.value}},
        "last_cognitive_analysis": {"processing_metadata": {"runtime_version": RuntimeVersion.V2.value}},
    }

    async def fake_get_diagnostics():
        return snapshot

    async def fake_get_traces():
        return []

    service.get_diagnostics = fake_get_diagnostics  # type: ignore[method-assign]
    service.get_active_traces = fake_get_traces  # type: ignore[method-assign]

    import asyncio

    observatory = asyncio.run(service.get_runtime_observatory())
    assert observatory["execution_blueprint"]["planning_metadata"]["runtime_version"] == RuntimeVersion.V2.value
    assert observatory["cognitive_analysis"]["processing_metadata"]["runtime_version"] == RuntimeVersion.V2.value


def test_execution_context_creation_contains_trace_metadata() -> None:
    context = create_execution_context(original_request={"message": "hi"}, runtime_version=RuntimeVersion.V2.value, request_id="req-789")
    assert context.execution_metadata is not None
    assert context.execution_metadata.request_id == "req-789"
    assert context.execution_state == ExecutionState.INITIALIZED.value
    assert context.trace_ids


def test_execution_state_machine_records_explicit_transitions() -> None:
    machine = ExecutionStateMachine()
    machine.transition_to(ExecutionState.READY, summary="prepared")
    machine.transition_to(ExecutionState.RUNNING, task_id="task_1", summary="started")
    machine.transition_to(ExecutionState.COMPLETED, task_id="task_1", summary="done")
    assert machine.current_state == ExecutionState.COMPLETED
    assert [transition.to_state for transition in machine.transitions] == [
        ExecutionState.INITIALIZED,
        ExecutionState.READY,
        ExecutionState.RUNNING,
        ExecutionState.COMPLETED,
    ]


def test_execution_tasks_are_built_from_execution_blueprint() -> None:
    cognitive_state = CognitiveEngine().analyze(
        request_text="Please implement a runtime execution engine.",
        runtime_version=RuntimeVersion.V2.value,
        request_id="req-task",
    )
    blueprint = PlanningEngine().plan(
        cognitive_state=cognitive_state,
        runtime_version=RuntimeVersion.V2.value,
        request_id="req-task",
    )
    tasks = build_execution_tasks(blueprint)
    assert len(tasks) >= len(blueprint.required_runtime_capabilities)
    assert tasks[0].task_id == "capability_1"
    assert tasks[0].required_capability
    assert any(task.required_capability == "provider" for task in tasks)


def test_capability_dispatcher_delegates_chat_to_v1_adapter() -> None:
    class DummyAdapter:
        async def execute_chat(self, **kwargs):
            return {"ok": True}

    task = ExecutionTask("task_1", "Dispatch", "Dispatch work", "analysis", ExecutionState.READY)
    context = create_execution_context(original_request={"message": "hi"}, runtime_version=RuntimeVersion.V2.value)
    dispatcher = CapabilityDispatcher(DummyAdapter())

    import asyncio

    response, result = asyncio.run(
        dispatcher.dispatch_chat(
            task=task,
            execution_context=context,
            payload={"message": "hi"},  # type: ignore[arg-type]
            current_user=object(),  # type: ignore[arg-type]
            organization_id=1,
        )
    )
    assert response == {"ok": True}
    assert result.task_id == "task_1"
    assert result.status == ExecutionState.COMPLETED


def test_native_capability_registry_resolves_builtin_executors() -> None:
    class DummyAdapter:
        async def execute_chat(self, **kwargs):
            return {"ok": True}

        async def execute_stream(self, **kwargs):
            if False:
                yield ""

    class DummyMemoryService:
        async def retrieve_memories(self, org_id, agent_id, query, top_k=5):
            return []

    class DummyKnowledgeService:
        def list_knowledge_bases(self, organization_id):
            return []

        def list_documents(self, kb_id):
            return []

    class DummyRAGService:
        async def retrieve_context(self, **kwargs):
            return "context"

    class DummyWorkflowService:
        async def execute_workflow(self, **kwargs):
            class Result:
                id = 1
                status = "COMPLETED"

            return Result()

    class DummyToolService:
        async def execute_batch(self, **kwargs):
            class Result:
                def model_dump(self):
                    return {"ok": True}

            return Result()

    class DummyProviderService:
        async def chat(self, *args, **kwargs):
            class Result:
                def model_dump(self):
                    return {"provider": True}

            return Result()

        async def list_models(self, *args, **kwargs):
            return ["model-a"]

    class DummyStreamingService:
        async def stream_new_chat(self, **kwargs):
            if False:
                yield ""

    registry = build_native_capability_registry(
        adapter=DummyAdapter(),
        memory_service=DummyMemoryService(),
        knowledge_service=DummyKnowledgeService(),
        rag_service=DummyRAGService(),
        workflow_service=DummyWorkflowService(),
        tool_execution_service=DummyToolService(),
        provider_service=DummyProviderService(),
        streaming_service=DummyStreamingService(),
    )
    assert registry.resolve("memory") is not None
    assert registry.resolve("provider") is not None


def test_capability_registry_resolves_registered_runtime() -> None:
    registry = CapabilityRegistry()

    class DummyRuntime:
        metadata = CapabilityMetadata(
            capability_id="memory",
            capability_name="Memory Runtime Adapter",
            version="1.0",
            supported_task_types=("memory",),
            dependencies=(),
            execution_mode=CapabilityExecutionMode.DELEGATED,
        )

    runtime = DummyRuntime()
    registry.register(runtime)  # type: ignore[arg-type]
    assert registry.resolve("memory") is runtime
    assert registry.metadata()[0].capability_name == "Memory Runtime Adapter"


def test_execution_engine_consumes_context_and_records_results() -> None:
    class DummyAdapter:
        async def execute_chat(self, **kwargs):
            return {"ok": True}

    cognitive_state = CognitiveEngine().analyze(
        request_text="Please implement a runtime execution engine.",
        runtime_version=RuntimeVersion.V2.value,
        request_id="req-engine",
    )
    blueprint = PlanningEngine().plan(
        cognitive_state=cognitive_state,
        runtime_version=RuntimeVersion.V2.value,
        request_id="req-engine",
    )
    context = create_execution_context(
        original_request={"message": "Please implement a runtime execution engine."},
        runtime_version=RuntimeVersion.V2.value,
        request_id="req-engine",
    ).with_updates(cognitive_state=cognitive_state, execution_blueprint=blueprint)

    import asyncio

    response = asyncio.run(
        ExecutionEngine(CapabilityDispatcher(DummyAdapter())).execute_chat(
            execution_context=context,
            payload={"message": "Please implement a runtime execution engine."},  # type: ignore[arg-type]
            current_user=object(),  # type: ignore[arg-type]
            organization_id=1,
        )
    )
    observatory = asyncio.run(ObservabilityService.__new__(ObservabilityService).get_diagnostics())
    assert response == {"ok": True}
    assert observatory["last_execution_engine"]["execution_state"] == ExecutionState.COMPLETED.value
    assert observatory["last_execution_engine"]["execution_results"][0]["task_id"] in {"capability_1", "capability_provider"}
    assert observatory["last_capability_event"]["stage_name"] == "Capability Resolution"


def test_dispatcher_falls_back_when_native_capability_is_missing() -> None:
    class DummyAdapter:
        async def execute_chat(self, **kwargs):
            return {"fallback": True}

        async def execute_stream(self, **kwargs):
            if False:
                yield ""

    task = ExecutionTask("task_legacy", "Legacy", "Legacy work", "legacy_capability", ExecutionState.READY)
    context = create_execution_context(original_request={"message": "hi"}, runtime_version=RuntimeVersion.V2.value)
    dispatcher = CapabilityDispatcher(DummyAdapter(), capability_registry=CapabilityRegistry())

    import asyncio

    response, result = asyncio.run(
        dispatcher.dispatch_chat(
            task=task,
            execution_context=context,
            payload={"message": "hi"},  # type: ignore[arg-type]
            current_user=object(),  # type: ignore[arg-type]
            organization_id=1,
        )
    )
    assert response == {"fallback": True}
    assert result.metadata["runtime"] == "RuntimeV1Adapter"
