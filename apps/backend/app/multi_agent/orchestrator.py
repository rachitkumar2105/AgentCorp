"""
Multi-agent orchestration helpers.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import Any

from app.observability.diagnostics import register_autonomous_execution
from app.runtime.goal_management import GoalEngine, GoalReport
from app.runtime.task_management import TaskManager, TaskQueue
from app.runtime.autonomous_execution import AutonomousExecutionEngine, ExecutionPolicy, AutonomousExecutionReport
from app.multi_agent.message_bus import message_bus


@dataclass(frozen=True)
class MultiAgentExecutionContext:
    goal: GoalReport
    participating_agents: tuple[int, ...]
    delegated_tasks: tuple[str, ...]
    shared_execution_state: dict[str, Any]
    shared_metadata: dict[str, Any]


@dataclass(frozen=True)
class MultiAgentOrchestrationReport:
    supervisor_agent_id: int
    goal: GoalReport
    autonomous_report: AutonomousExecutionReport
    shared_context: MultiAgentExecutionContext
    aggregation_summary: str
    started_at: str
    completed_at: str
    duration: float
    metadata: dict[str, Any]


class ResultAggregator:
    def aggregate(self, report: AutonomousExecutionReport) -> dict[str, Any]:
        return {
            "goal_id": report.goal.goal_id,
            "completed_tasks": [task.task_id for task in report.completed_tasks],
            "failed_tasks": [task.task_id for task in report.failed_tasks],
            "blocked_tasks": [task.task_id for task in report.blocked_tasks],
            "progress_percent": report.progress_percent,
            "summary": report.summary,
            "provenance": report.metadata,
        }


class MultiAgentOrchestrator:
    def __init__(self, runtime_v2: Any, multi_agent_service: Any, task_manager: TaskManager | None = None) -> None:
        self.runtime_v2 = runtime_v2
        self.multi_agent_service = multi_agent_service
        self.task_manager = task_manager or TaskManager()
        self.goal_engine = GoalEngine()
        self.execution_policy = ExecutionPolicy()
        self.autonomous_execution_engine = AutonomousExecutionEngine(runtime_v2, task_manager=self.task_manager, execution_policy=self.execution_policy)
        self.aggregator = ResultAggregator()

    async def orchestrate_goal(self, *, goal: GoalReport, supervisor_agent_id: int, worker_agent_ids: tuple[int, ...], current_user: Any, organization_id: int, session_id: int) -> MultiAgentOrchestrationReport:
        started_at = datetime.now(timezone.utc)
        delegated_tasks = tuple(task.task_id or "" for task in self.task_manager.split_goal(goal))
        shared_context = MultiAgentExecutionContext(
            goal=goal,
            participating_agents=(supervisor_agent_id,) + worker_agent_ids,
            delegated_tasks=delegated_tasks,
            shared_execution_state={"status": "running"},
            shared_metadata={"organization_id": organization_id},
        )
        queue = TaskQueue()
        for task in self.task_manager.split_goal(goal):
            queue.enqueue(task)
        await message_bus.publish(
            session_id,
            {"event": "supervisor_started", "goal_id": goal.goal_id, "supervisor_agent_id": supervisor_agent_id},
        )
        await message_bus.publish(
            session_id,
            {"event": "task_delegation", "goal_id": goal.goal_id, "delegated_tasks": shared_context.delegated_tasks},
        )
        autonomous_report = await self.autonomous_execution_engine.execute_goal(goal=goal, current_user=current_user, organization_id=organization_id)
        aggregated = self.aggregator.aggregate(autonomous_report)
        completed_at = datetime.now(timezone.utc)
        await register_autonomous_execution(
            str(goal.goal_id or "goal"),
            {
                "status": "multi_agent_completed",
                "goal_id": goal.goal_id,
                "supervisor_agent_id": supervisor_agent_id,
                "worker_agent_ids": worker_agent_ids,
                "aggregation_summary": aggregated["summary"],
            },
        )
        return MultiAgentOrchestrationReport(
            supervisor_agent_id=supervisor_agent_id,
            goal=replace(autonomous_report.goal, metadata={**autonomous_report.goal.metadata, "aggregation": aggregated}),
            autonomous_report=autonomous_report,
            shared_context=shared_context,
            aggregation_summary=aggregated["summary"],
            started_at=started_at.isoformat(),
            completed_at=completed_at.isoformat(),
            duration=(completed_at - started_at).total_seconds(),
            metadata={"organization_id": organization_id, "worker_agent_count": len(worker_agent_ids)},
        )
