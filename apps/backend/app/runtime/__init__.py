"""
Runtime routing and version contracts.
"""

from app.runtime.contract import RuntimeContract
from app.runtime.cognitive import CognitiveEngine, CognitiveState
from app.runtime.capabilities import CapabilityMetadata, CapabilityRegistry, CapabilityRuntime
from app.runtime.dispatcher import CapabilityDispatcher
from app.runtime.engine import ExecutionEngine
from app.runtime.execution import ExecutionResult, ExecutionState, ExecutionStateMachine, ExecutionTask
from app.runtime.evaluation import EvaluationEngine, EvaluationReport
from app.runtime.autonomous_execution import AutonomousExecutionEngine, AutonomousExecutionReport, ExecutionPolicy, ExecutionPolicyDecision, ExecutionDecision
from app.runtime.goal_management import GoalEngine, GoalLifecycleState, GoalMilestone, GoalPriority, GoalReport, GoalTraceEntry
from app.runtime.learning import LearningArtifact, LearningDecision, LearningEngine, LearningPolicy, LearningPolicyDecision, LearningReport
from app.runtime.observatory import RuntimeObservatoryEngine, ObservatoryEdge, ObservatoryNode, TimelineEntry
from app.runtime.optimization import OptimizationPolicy, RuntimeOptimizationEngine, RuntimeOptimizationReport, OptimizationRecommendation
from app.runtime.governance import ApprovalEngine, ApprovalResult, ApprovalState, ComplianceEngine, ComplianceResult, ExecutionGuard, ExecutionGuardResult, GovernanceDecision, GovernanceEngine, GovernanceReport, PolicyEngine, PolicyResult
from app.runtime.long_term_intelligence import (
    CapabilityScoringEngine,
    ForgettingPolicy,
    LongTermIntelligenceEngine,
    LongTermIntelligenceReport,
    LongTermKnowledge,
    MemoryConsolidationEngine,
    PatternDiscoveryEngine,
    PreferenceEvolutionEngine,
)
from app.runtime.task_management import TaskDependency, TaskLifecycleState, TaskManager, TaskMilestone, TaskQueue, TaskQueueSnapshot, TaskReport
from app.runtime.reflection import ReflectionEngine, ReflectionReport
from app.runtime.planning import ExecutionBlueprint, PlanningEngine
from app.runtime.router import RuntimeRouter, RuntimeVersion

__all__ = [
    "RuntimeContract",
    "CognitiveEngine",
    "CognitiveState",
    "CapabilityMetadata",
    "CapabilityRegistry",
    "CapabilityRuntime",
    "CapabilityDispatcher",
    "ExecutionEngine",
    "ExecutionResult",
    "ExecutionState",
    "ExecutionStateMachine",
    "ExecutionTask",
    "EvaluationEngine",
    "EvaluationReport",
    "AutonomousExecutionEngine",
    "AutonomousExecutionReport",
    "ExecutionPolicy",
    "ExecutionPolicyDecision",
    "ExecutionDecision",
    "GoalEngine",
    "GoalLifecycleState",
    "GoalMilestone",
    "GoalPriority",
    "GoalReport",
    "GoalTraceEntry",
    "TaskDependency",
    "TaskLifecycleState",
    "TaskManager",
    "TaskMilestone",
    "TaskQueue",
    "TaskQueueSnapshot",
    "TaskReport",
    "LearningArtifact",
    "LearningDecision",
    "LearningEngine",
    "LearningPolicy",
    "LearningPolicyDecision",
    "LearningReport",
    "RuntimeObservatoryEngine",
    "ObservatoryNode",
    "ObservatoryEdge",
    "TimelineEntry",
    "OptimizationPolicy",
    "RuntimeOptimizationEngine",
    "RuntimeOptimizationReport",
    "OptimizationRecommendation",
    "ApprovalEngine",
    "ApprovalResult",
    "ApprovalState",
    "ComplianceEngine",
    "ComplianceResult",
    "ExecutionGuard",
    "ExecutionGuardResult",
    "GovernanceDecision",
    "GovernanceEngine",
    "GovernanceReport",
    "PolicyEngine",
    "PolicyResult",
    "CapabilityScoringEngine",
    "ForgettingPolicy",
    "LongTermIntelligenceEngine",
    "LongTermIntelligenceReport",
    "LongTermKnowledge",
    "MemoryConsolidationEngine",
    "PatternDiscoveryEngine",
    "PreferenceEvolutionEngine",
    "ExecutionBlueprint",
    "PlanningEngine",
    "ReflectionEngine",
    "ReflectionReport",
    "RuntimeRouter",
    "RuntimeVersion",
]
