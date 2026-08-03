"""
Agent Engine — Service Layer.

Orchestrates Planning, Reasoning, Decision-making and execution routing.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any
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
from app.runtime.goal_management import GoalEngine
from app.runtime.task_management import TaskManager

# Delegate targets from other modules
from app.services.chat_service import ChatService
from app.services.tool_service import ToolService
from app.services.memory_service import MemoryService
from app.services.rag_service import RAGService
from app.services.workflow_service import WorkflowService
from app.services.tool_execution_service import ToolExecutionService
from app.services.knowledge_service import KnowledgeService
from app.schemas.tool_execution import ToolCallRequest

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
        self.goal_engine = GoalEngine()
        self.task_manager = TaskManager()

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

        goal_report = self.goal_engine.from_db(goal)
        decomposed_tasks = self.task_manager.split_goal(goal_report)
        for index, t in enumerate(decomposed_tasks):
            task = GoalTask(
                goal_id=goal.id,
                title=t.title,
                description=t.description,
                status=t.status.value,
                priority=t.priority.value,
                order=index,
                execution_type=t.capability,
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

        tasks = self.task_repo.list_by_goal(goal_id)

        # Create execution tracking entry
        execution = AgentExecution(
            goal_id=goal_id,
            organization_id=organization_id,
            status="RUNNING",
            execution_context={
                "iterations": 0,
                "status": "active",
                "objective": goal.objective,
                "plan": [
                    {
                        "task_id": task.id,
                        "title": task.title,
                        "description": task.description,
                        "execution_type": task.execution_type,
                    }
                    for task in tasks
                ],
                "task_results": [],
                "reflections": [],
                "evaluations": [],
            },
        )
        execution = self.exec_repo.create(execution)

        start_time = time.perf_counter()

        # Main agent loops runs
        iteration = 0
        max_iterations = max(len(tasks), 1)
        goal_achieved = False

        while iteration < max_iterations and not goal_achieved:
            iteration += 1
            context = dict(execution.execution_context or {})
            context["iterations"] = iteration
            execution.execution_context = context

            current_task = next((task for task in tasks if task.status != "COMPLETED"), None)
            if current_task is None:
                break

            # 1. Reason on state
            reasoning = self.reasoner.reason_state(
                f"{goal.objective}\n{current_task.description or current_task.title}",
                execution.execution_context,
            )

            # 2. Select next action type
            action = self.decision_engine.select_action(reasoning, execution.execution_context)
            action = self._override_action_from_task(current_task.execution_type, action)

            # 3. Execution routing
            task_output = await self._execute_action(
                action=action,
                goal=goal,
                task=current_task,
                current_user=current_user,
            )
            output_msg = task_output.get("summary", str(task_output))

            # 4. Reflect on the result
            reflection = self.reflection.reflect_outcome(output_msg, goal.success_criteria)
            goal_achieved = self.evaluator.is_goal_achieved(goal.objective, reflection)
            evaluation = {
                "task_id": current_task.id,
                "action": action.value,
                "goal_achieved": goal_achieved,
                "success": task_output.get("success", True),
            }

            # Update task states
            current_task.status = "COMPLETED" if task_output.get("success", True) else "FAILED"
            self.task_repo.update(current_task)

            # Save checkpoint state mapping
            context = dict(execution.execution_context or {})
            context.setdefault("task_results", []).append(task_output)
            context.setdefault("reflections", []).append(reflection)
            context.setdefault("evaluations", []).append(evaluation)
            context["last_reasoning"] = reasoning
            context["last_action"] = action.value
            context["status"] = "completed" if goal_achieved else "active"
            execution.execution_context = context
            self.exec_repo.update(execution)

            if task_output.get("success") is False and not reflection.get("replanning_needed", False):
                break

        all_tasks_completed = all(task.status == "COMPLETED" for task in tasks)
        execution.status = "COMPLETED" if goal_achieved or all_tasks_completed else "FAILED"
        execution.completed_at = datetime.now(timezone.utc)
        execution.duration = time.perf_counter() - start_time
        self.exec_repo.update(execution)

        # Update Goal status
        goal.status = execution.status
        self.goal_repo.update(goal)

        return execution

    def _override_action_from_task(self, execution_type: str, fallback: ActionType) -> ActionType:
        normalized = (execution_type or "").lower()
        if "tool" in normalized:
            return ActionType.EXECUTE_TOOL
        if "workflow" in normalized:
            return ActionType.RUN_WORKFLOW
        if "rag" in normalized or "knowledge" in normalized:
            return ActionType.SEARCH_KNOWLEDGE
        if "memory" in normalized:
            return ActionType.SEARCH_MEMORY
        return fallback

    async def _execute_action(
        self,
        *,
        action: ActionType,
        goal: Goal,
        task: GoalTask,
        current_user: User,
    ) -> dict[str, Any]:
        query = task.description or task.title or goal.objective
        if action == ActionType.SEARCH_MEMORY:
            memories = await MemoryService(self.db).retrieve_memories(
                org_id=goal.organization_id,
                agent_id=goal.agent_id,
                query=query,
                top_k=5,
            )
            return {
                "success": True,
                "task_id": task.id,
                "summary": f"Retrieved {len(memories)} memory item(s).",
                "memories": [
                    {"id": memory.id, "title": memory.title, "content": memory.content}
                    for memory in memories
                ],
            }
        if action == ActionType.SEARCH_KNOWLEDGE:
            contexts: list[dict[str, Any]] = []
            knowledge_bases = KnowledgeService(self.db).list_knowledge_bases(goal.organization_id)
            for kb in knowledge_bases:
                context = await RAGService(self.db).retrieve_context(kb.id, query, top_k=5, max_tokens=2000)
                if context:
                    contexts.append({"knowledge_base_id": kb.id, "name": kb.name, "context": context})
            return {
                "success": True,
                "task_id": task.id,
                "summary": f"Retrieved context from {len(contexts)} knowledge base(s).",
                "knowledge_contexts": contexts,
            }
        if action == ActionType.EXECUTE_TOOL:
            tool_name = self._extract_metadata_value(task.description, "tool_name")
            if not tool_name:
                return {
                    "success": False,
                    "task_id": task.id,
                    "placeholder": True,
                    "summary": "Tool execution requires task metadata containing tool_name.",
                }
            result = await ToolExecutionService(self.db).execute_batch(
                requests=[ToolCallRequest(call_id=f"agent-task-{task.id}", tool_name=tool_name, arguments={})],
                current_user=current_user,
                organization_id=goal.organization_id,
                agent_id=goal.agent_id,
                conversation_id=goal.conversation_id or 0,
            )
            return {
                "success": result.all_succeeded,
                "task_id": task.id,
                "summary": f"Executed tool '{tool_name}'.",
                "tool_results": [item.model_dump() for item in result.results],
            }
        if action == ActionType.RUN_WORKFLOW:
            workflow_id = self._extract_metadata_value(task.description, "workflow_id")
            if not workflow_id:
                return {
                    "success": False,
                    "task_id": task.id,
                    "placeholder": True,
                    "summary": "Workflow execution requires task metadata containing workflow_id.",
                }
            workflow_execution = await WorkflowService(self.db).execute_workflow(
                workflow_id=int(workflow_id),
                organization_id=goal.organization_id,
                agent_id=goal.agent_id,
                current_user=current_user,
            )
            return {
                "success": workflow_execution.status == "COMPLETED",
                "task_id": task.id,
                "summary": f"Workflow execution {workflow_execution.id} finished with {workflow_execution.status}.",
                "workflow_execution_id": workflow_execution.id,
            }
        return {
            "success": True,
            "task_id": task.id,
            "summary": "Reasoning cycle completed with existing planner/reasoner components.",
            "placeholder": action == ActionType.THINK,
        }

    def _extract_metadata_value(self, text: str | None, key: str) -> str | None:
        if not text:
            return None
        marker = f"{key}="
        for part in text.replace("\n", " ").split():
            if part.startswith(marker):
                return part.removeprefix(marker).strip(" ,;")
        return None

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
