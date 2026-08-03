"""
Runtime V2 task management layer.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from app.runtime.goal_management import GoalLink, GoalPriority, GoalReport, GoalLifecycleState, GoalMilestone


class TaskLifecycleState(str, Enum):
    CREATED = "CREATED"
    READY = "READY"
    BLOCKED = "BLOCKED"
    WAITING = "WAITING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True)
class TaskDependency:
    task_id: str
    relation: str


@dataclass(frozen=True)
class TaskScheduleMetadata:
    earliest_start: str | None = None
    latest_finish: str | None = None
    deadline: str | None = None
    retry_eligible: bool = True
    estimated_duration_minutes: int | None = None


@dataclass(frozen=True)
class TaskMilestone:
    title: str
    description: str | None
    achieved: bool
    achieved_at: str | None = None


@dataclass(frozen=True)
class TaskReport:
    task_id: str | None
    goal_id: int | None
    parent_task_id: str | None
    child_task_ids: tuple[str, ...]
    title: str
    description: str | None
    capability: str
    priority: GoalPriority
    status: TaskLifecycleState
    dependencies: tuple[TaskDependency, ...]
    estimated_duration_minutes: int | None
    schedule: TaskScheduleMetadata
    milestones: tuple[TaskMilestone, ...]
    created_at: str
    updated_at: str
    completed_at: str | None
    metadata: dict[str, Any]


@dataclass(frozen=True)
class TaskQueueEntry:
    task: TaskReport
    queue_position: int


@dataclass(frozen=True)
class TaskQueueSnapshot:
    queue_size: int
    ready_count: int
    blocked_count: int
    completed_count: int
    dependency_summary: dict[str, int]
    task_priority_summary: dict[str, int]
    queued_tasks: tuple[TaskReport, ...]


class TaskQueue:
    def __init__(self) -> None:
        self._entries: list[TaskReport] = []

    def enqueue(self, task: TaskReport) -> None:
        self._entries.append(task)
        self._entries = list(self._ordered(self._entries))

    def dequeue(self) -> TaskReport | None:
        if not self._entries:
            return None
        return self._entries.pop(0)

    def inspect(self) -> TaskQueueSnapshot:
        return self._snapshot(self._entries)

    def reorder(self, tasks: tuple[TaskReport, ...]) -> None:
        self._entries = list(self._ordered(list(tasks)))

    @staticmethod
    def _ordered(tasks: list[TaskReport]) -> tuple[TaskReport, ...]:
        rank = {GoalPriority.URGENT: 0, GoalPriority.HIGH: 1, GoalPriority.MEDIUM: 2, GoalPriority.LOW: 3}
        return tuple(sorted(
            tasks,
            key=lambda task: (
                task.status != TaskLifecycleState.READY,
                rank[task.priority],
                task.schedule.deadline or "9999-12-31T23:59:59+00:00",
                task.created_at,
                task.task_id or "",
            ),
        ))

    @staticmethod
    def _snapshot(tasks: list[TaskReport]) -> TaskQueueSnapshot:
        return TaskQueueSnapshot(
            queue_size=len(tasks),
            ready_count=sum(1 for task in tasks if task.status == TaskLifecycleState.READY),
            blocked_count=sum(1 for task in tasks if task.status == TaskLifecycleState.BLOCKED),
            completed_count=sum(1 for task in tasks if task.status == TaskLifecycleState.COMPLETED),
            dependency_summary={
                "with_dependencies": sum(1 for task in tasks if task.dependencies),
                "without_dependencies": sum(1 for task in tasks if not task.dependencies),
            },
            task_priority_summary={
                priority.value: sum(1 for task in tasks if task.priority == priority)
                for priority in GoalPriority
            },
            queued_tasks=tuple(tasks),
        )


class TaskManager:
    def create_tasks(self, *, goal: GoalReport) -> tuple[TaskReport, ...]:
        created_at = datetime.now(timezone.utc).isoformat()
        tasks: list[TaskReport] = []
        base_count = max(1, min(3, len(goal.objective.split()) // 4 or 1))
        for index in range(base_count):
            task_id = f"{goal.goal_id or 'goal'}-task-{index + 1}"
            dependency = (TaskDependency(task_id=f"{goal.goal_id or 'goal'}-task-{index}", relation="prerequisite"),) if index > 0 else ()
            tasks.append(
                TaskReport(
                    task_id=task_id,
                    goal_id=goal.goal_id,
                    parent_task_id=None,
                    child_task_ids=(),
                    title=f"{goal.title} - Step {index + 1}",
                    description=goal.objective if index == 0 else f"Continue: {goal.objective}",
                    capability="analysis" if index == 0 else "planning",
                    priority=goal.priority,
                    status=TaskLifecycleState.READY if index == 0 else TaskLifecycleState.BLOCKED,
                    dependencies=dependency,
                    estimated_duration_minutes=15 + index * 10,
                    schedule=TaskScheduleMetadata(
                        earliest_start=created_at,
                        latest_finish=None,
                        deadline=goal.metadata.get("deadline") if goal.metadata else None,
                        retry_eligible=True,
                        estimated_duration_minutes=15 + index * 10,
                    ),
                    milestones=(),
                    created_at=created_at,
                    updated_at=created_at,
                    completed_at=None,
                    metadata={"goal_objective": goal.objective, **goal.metadata},
                )
            )
        return tuple(tasks)

    def split_goal(self, goal: GoalReport) -> tuple[TaskReport, ...]:
        return self.create_tasks(goal=goal)

    def update_task(self, task: TaskReport, *, status: TaskLifecycleState | None = None, metadata: dict[str, Any] | None = None) -> TaskReport:
        return replace(
            task,
            status=status or task.status,
            updated_at=datetime.now(timezone.utc).isoformat(),
            completed_at=datetime.now(timezone.utc).isoformat() if status == TaskLifecycleState.COMPLETED else task.completed_at,
            metadata={**task.metadata, **(metadata or {})},
        )

    def cancel_task(self, task: TaskReport) -> TaskReport:
        return self.update_task(task, status=TaskLifecycleState.CANCELLED)

    def complete_task(self, task: TaskReport) -> TaskReport:
        return self.update_task(task, status=TaskLifecycleState.COMPLETED)

    def prioritize_tasks(self, tasks: tuple[TaskReport, ...]) -> tuple[TaskReport, ...]:
        return TaskQueue._ordered(list(tasks))

    def validate_dependencies(self, task: TaskReport, completed_task_ids: set[str]) -> bool:
        return all(dep.task_id in completed_task_ids for dep in task.dependencies)

    def ready_tasks(self, tasks: tuple[TaskReport, ...]) -> tuple[TaskReport, ...]:
        return tuple(task for task in self.prioritize_tasks(tasks) if task.status == TaskLifecycleState.READY)

    def blocked_tasks(self, tasks: tuple[TaskReport, ...]) -> tuple[TaskReport, ...]:
        return tuple(task for task in tasks if task.status == TaskLifecycleState.BLOCKED)

    def analyze_goal(self, goal: GoalReport) -> TaskReport | None:
        tasks = self.create_tasks(goal=goal)
        return tasks[0] if tasks else None

    def build_dependency_graph(self, tasks: tuple[TaskReport, ...]) -> dict[str, tuple[str, ...]]:
        return {task.task_id or f"task-{index}": tuple(dep.task_id for dep in task.dependencies) for index, task in enumerate(tasks)}

    def queue_snapshot(self, tasks: tuple[TaskReport, ...]) -> TaskQueueSnapshot:
        queue = TaskQueue()
        for task in tasks:
            queue.enqueue(task)
        return queue.inspect()

