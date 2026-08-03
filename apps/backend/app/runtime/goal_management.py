"""
Runtime V2 goal management layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from app.models.goal import Goal


class GoalLifecycleState(str, Enum):
    CREATED = "CREATED"
    ANALYZED = "ANALYZED"
    PLANNED = "PLANNED"
    READY = "READY"
    ACTIVE = "ACTIVE"
    BLOCKED = "BLOCKED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class GoalPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@dataclass(frozen=True)
class GoalLink:
    goal_id: int
    relation: str


@dataclass(frozen=True)
class GoalMilestone:
    title: str
    description: str | None
    achieved: bool
    achieved_at: str | None = None


@dataclass(frozen=True)
class GoalTraceEntry:
    stage_name: str
    status: str
    summary: str
    goal_id: int | None
    created_at: str
    updated_at: str | None = None
    priority: str | None = None
    dependencies: tuple[GoalLink, ...] = ()
    milestones: tuple[GoalMilestone, ...] = ()
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class GoalReport:
    goal_id: int | None
    title: str
    description: str | None
    objective: str
    owner_id: int | None
    organization_id: int | None
    priority: GoalPriority
    status: GoalLifecycleState
    dependencies: tuple[GoalLink, ...]
    parent_goal_id: int | None
    child_goal_ids: tuple[int, ...]
    milestones: tuple[GoalMilestone, ...]
    created_at: str
    updated_at: str
    completed_at: str | None
    metadata: dict[str, Any]


class GoalEngine:
    def create_goal(
        self,
        *,
        title: str,
        objective: str,
        owner_id: int,
        organization_id: int,
        description: str | None = None,
        priority: GoalPriority = GoalPriority.MEDIUM,
        parent_goal_id: int | None = None,
        dependencies: tuple[GoalLink, ...] = (),
        metadata: dict[str, Any] | None = None,
    ) -> GoalReport:
        now = datetime.now(timezone.utc).isoformat()
        return GoalReport(
            goal_id=None,
            title=title,
            description=description,
            objective=objective,
            owner_id=owner_id,
            organization_id=organization_id,
            priority=priority,
            status=GoalLifecycleState.CREATED,
            dependencies=dependencies,
            parent_goal_id=parent_goal_id,
            child_goal_ids=(),
            milestones=(),
            created_at=now,
            updated_at=now,
            completed_at=None,
            metadata=metadata or {},
        )

    def update_goal(self, goal: GoalReport, *, status: GoalLifecycleState | None = None, priority: GoalPriority | None = None, milestones: tuple[GoalMilestone, ...] | None = None, metadata: dict[str, Any] | None = None) -> GoalReport:
        updated_at = datetime.now(timezone.utc).isoformat()
        completed_at = goal.completed_at
        if status in {GoalLifecycleState.COMPLETED, GoalLifecycleState.CANCELLED, GoalLifecycleState.FAILED}:
            completed_at = updated_at
        return GoalReport(
            goal_id=goal.goal_id,
            title=goal.title,
            description=goal.description,
            objective=goal.objective,
            owner_id=goal.owner_id,
            organization_id=goal.organization_id,
            priority=priority or goal.priority,
            status=status or goal.status,
            dependencies=goal.dependencies,
            parent_goal_id=goal.parent_goal_id,
            child_goal_ids=goal.child_goal_ids,
            milestones=milestones or goal.milestones,
            created_at=goal.created_at,
            updated_at=updated_at,
            completed_at=completed_at,
            metadata={**goal.metadata, **(metadata or {})},
        )

    def close_goal(self, goal: GoalReport, *, completed: bool = True) -> GoalReport:
        return self.update_goal(goal, status=GoalLifecycleState.COMPLETED if completed else GoalLifecycleState.FAILED)

    def cancel_goal(self, goal: GoalReport) -> GoalReport:
        return self.update_goal(goal, status=GoalLifecycleState.CANCELLED)

    def prioritize_goals(self, goals: tuple[GoalReport, ...]) -> tuple[GoalReport, ...]:
        rank = {GoalPriority.URGENT: 0, GoalPriority.HIGH: 1, GoalPriority.MEDIUM: 2, GoalPriority.LOW: 3}
        return tuple(sorted(goals, key=lambda goal: (rank[goal.priority], goal.created_at, goal.goal_id or 0)))

    def validate_dependencies(self, goal: GoalReport, existing_goal_ids: set[int]) -> bool:
        return all(link.goal_id in existing_goal_ids for link in goal.dependencies)

    def track_milestone(self, goal: GoalReport, milestone: GoalMilestone) -> GoalReport:
        return self.update_goal(goal, milestones=goal.milestones + (milestone,))

    def analyze_goal(self, goal: GoalReport) -> GoalTraceEntry:
        return GoalTraceEntry(
            stage_name=f"Goal {goal.status.value.title()}",
            status=goal.status.value,
            summary=f"Goal '{goal.title}' is {goal.status.value.lower()} with priority {goal.priority.value}.",
            goal_id=goal.goal_id,
            created_at=goal.created_at,
            updated_at=goal.updated_at,
            priority=goal.priority.value,
            dependencies=goal.dependencies,
            milestones=goal.milestones,
            metadata=goal.metadata,
        )

    @staticmethod
    def from_db(goal: Goal, *, child_goal_ids: tuple[int, ...] = (), dependency_ids: tuple[int, ...] = ()) -> GoalReport:
        now = goal.updated_at.isoformat() if getattr(goal, "updated_at", None) else datetime.now(timezone.utc).isoformat()
        created = goal.created_at.isoformat() if getattr(goal, "created_at", None) else now
        deps = tuple(GoalLink(goal_id=dep_id, relation="dependency") for dep_id in dependency_ids)
        return GoalReport(
            goal_id=goal.id,
            title=goal.title,
            description=goal.description,
            objective=goal.objective,
            owner_id=goal.created_by,
            organization_id=goal.organization_id,
            priority=_priority_from_string(goal.priority),
            status=_status_from_string(goal.status),
            dependencies=deps,
            parent_goal_id=None,
            child_goal_ids=child_goal_ids,
            milestones=(),
            created_at=created,
            updated_at=now,
            completed_at=goal.updated_at.isoformat() if goal.status in {"COMPLETED", "CANCELLED", "FAILED"} and getattr(goal, "updated_at", None) else None,
            metadata={"success_criteria": goal.success_criteria, "constraints": goal.constraints or {}},
        )


def _priority_from_string(value: str) -> GoalPriority:
    normalized = (value or "").lower()
    if normalized in {"urgent", "high", "medium", "low"}:
        return GoalPriority(normalized)
    return GoalPriority.MEDIUM


def _status_from_string(value: str) -> GoalLifecycleState:
    normalized = (value or "").upper()
    if normalized in GoalLifecycleState.__members__:
        return GoalLifecycleState[normalized]
    return GoalLifecycleState.CREATED
