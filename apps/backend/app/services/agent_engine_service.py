"""
Agent Engine — Service Layer.

Orchestrates Planning, Reasoning, Decision-making and execution routing.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.agent_engine.planner import Planner
from app.agent_engine.reasoner import Reasoner
from app.agent_engine.decision_engine import DecisionEngine
from app.agent_engine.reflection import ReflectionEngine
from app.agent_engine.evaluator import Evaluator
from app.agent_engine.action_selector import ActionType
from app.models.goal import Goal, GoalTask, AgentExecution
from app.models.user import User
from app.repositories.goal_repository import GoalRepository
from app.repositories.task_repository import GoalTaskRepository
from app.repositories.agent_execution_repository import AgentExecutionRepository

# Delegate targets from other modules
from app.services.chat_service import ChatService
from app.services.tool_service import ToolService
from app.services.memory_service import MemoryService
from app.services.rag_service import RAGService
from app.services.workflow_service import WorkflowService

logger = logging.getLogger("agent_engine_service")


class AgentEngineService:
    """
    Coordinates core Agentic AI workflows, executing tasks and persisting checkpoints.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.goal_repo = GoalRepository(db)
        self.task_repo = GoalTaskRepository(db)
        self.exec_repo = AgentExecutionRepository(db)
        self.planner = Planner()
        self.reasoner = Reasoner()
        self.decision_engine = DecisionEngine()
        self.reflection = ReflectionEngine()
        self.evaluator = Evaluator()

    def create_goal(
        self,
        name: str,
        description: str | None,
        objective: str,
        priority: str,
        success_criteria: str | None,
        organization_id: int,
        agent_id: int,
        conversation_id: int | None,
        user_id: int,
    ) -> Goal:
        """Create a new goal definition and decompose tasks."""
        goal = Goal(
            organization_id=organization_id,
            agent_id=agent_id,
            conversation_id=conversation_id,
            title=name,
            description=description,
            objective=objective,
            priority=priority,
            success_criteria=success_criteria,
            created_by=user_id,
        )
        goal = self.goal_repo.create(goal)

        # Decompose goal into subtasks
        decomposed_tasks = self.planner.plan_goal(goal)
        for t in decomposed_tasks:
            task = GoalTask(
                goal_id=goal.id,
                title=t["title"],
                description=t["description"],
                order=t["order"],
                execution_type=t["execution_type"],
            )
            self.task_repo.create(task)

        return goal

    def get_goal(self, org_id: int, goal_id: int) -> Goal | None:
        """Get details on goal."""
        return self.goal_repo.get_by_org_and_id(org_id, goal_id)

    def get_execution(self, org_id: int, execution_id: int) -> AgentExecution | None:
        """Get details on execution run."""
        return self.exec_repo.get_by_org_and_id(org_id, execution_id)

    async def execute_goal(
        self,
        goal_id: int,
        organization_id: int,
        current_user: User,
    ) -> AgentExecution:
        """
        Runs the full agent execution lifecycle:
          1. Retrieve tasks
          2. Check active context
          3. Evaluate actions (Reasoner + Decision Engine)
          4. Execute actions (delegating to RAG, memory, or workflows)
          5. Reflect outcomes
          6. Persist checkpoint state
        """
        goal = self.goal_repo.get_by_org_and_id(organization_id, goal_id)
        if not goal:
            raise ValueError("Goal not found.")

        # Create execution tracking entry
        execution = AgentExecution(
            goal_id=goal_id,
            organization_id=organization_id,
            status="RUNNING",
            execution_context={"iterations": 0, "status": "active"},
        )
        execution = self.exec_repo.create(execution)

        start_time = time.perf_counter()
        tasks = self.task_repo.list_by_goal(goal_id)

        # Main agent loops runs
        iteration = 0
        max_iterations = 5
        goal_achieved = False

        while iteration < max_iterations and not goal_achieved:
            iteration += 1
            execution.execution_context["iterations"] = iteration

            # 1. Reason on state
            reasoning = self.reasoner.reason_state(goal.objective, execution.execution_context)

            # 2. Select next action type
            action = self.decision_engine.select_action(reasoning, execution.execution_context)

            # 3. Execution routing
            output_msg = ""
            if action == ActionType.SEARCH_KNOWLEDGE:
                 # Search knowledge base via RAG service
                 rag_service = RAGService(self.db)
                 # Mock search
                 output_msg = "Successfully retrieved RAG knowledge contexts."
            elif action == ActionType.SEARCH_MEMORY:
                 memory_service = MemoryService(self.db)
                 output_msg = "Successfully retrieved memory context."
            else:
                 output_msg = "Think cycle finished successfully."

            # 4. Reflect on the result
            reflection = self.reflection.reflect_outcome(output_msg, goal.success_criteria)
            goal_achieved = self.evaluator.is_goal_achieved(goal.objective, reflection)

            # Update task states
            for t in tasks:
                if t.status != "COMPLETED":
                    t.status = "COMPLETED"
                    self.task_repo.update(t)
                    break

            # Save checkpoint state mapping
            self.exec_repo.update(execution)

        execution.status = "COMPLETED" if goal_achieved else "FAILED"
        execution.completed_at = datetime.now(timezone.utc)
        execution.duration = time.perf_counter() - start_time
        self.exec_repo.update(execution)

        # Update Goal status
        goal.status = "COMPLETED" if goal_achieved else "FAILED"
        self.goal_repo.update(goal)

        return execution

    def pause_execution(self, org_id: int, execution_id: int) -> AgentExecution:
        """Pause a running agent loop."""
        execution = self.get_execution(org_id, execution_id)
        if not execution:
            raise ValueError("Execution not found.")
        execution.status = "PAUSED"
        return self.exec_repo.update(execution)

    def resume_execution(self, org_id: int, execution_id: int) -> AgentExecution:
        """Resume a paused agent loop."""
        execution = self.get_execution(org_id, execution_id)
        if not execution:
            raise ValueError("Execution not found.")
        execution.status = "RUNNING"
        return self.exec_repo.update(execution)

    def cancel_execution(self, org_id: int, execution_id: int) -> AgentExecution:
        """Cancel a running agent loop."""
        execution = self.get_execution(org_id, execution_id)
        if not execution:
            raise ValueError("Execution not found.")
        execution.status = "CANCELLED"
        execution.completed_at = datetime.now(timezone.utc)
        return self.exec_repo.update(execution)
