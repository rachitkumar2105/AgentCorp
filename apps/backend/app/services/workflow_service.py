"""
Workflow Engine — Service Layer.

Orchestrates execution context state loops and calls related services.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any
from sqlalchemy.orm import Session

from app.models.workflow import Workflow, WorkflowNode, WorkflowEdge, WorkflowExecution, WorkflowStep
from app.models.user import User
from app.repositories.workflow_repository import WorkflowRepository
from app.repositories.workflow_execution_repository import WorkflowExecutionRepository
from app.services.chat_service import ChatService
from app.services.tool_service import ToolService
from app.services.memory_service import MemoryService
from app.services.rag_service import RAGService
from app.services.tool_execution_service import ToolExecutionService
from app.schemas.tool_execution import ToolCallRequest
from app.workflow.transition import TransitionEngine
from app.workflow.validator import WorkflowValidator

logger = logging.getLogger("workflow_service")


class WorkflowService:
    """
    Coordinates workflow graph builds and executes node transitions.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.workflow_repo = WorkflowRepository(db)
        self.execution_repo = WorkflowExecutionRepository(db)
        self.validator = WorkflowValidator()
        self.transition_engine = TransitionEngine()

    def create_workflow(
        self,
        name: str,
        description: str | None,
        version: str,
        organization_id: int,
        user_id: int,
        nodes: list[dict],
        edges: list[dict],
    ) -> Workflow:
        """Create a new logical workflow graph definition."""
        workflow = Workflow(
            organization_id=organization_id,
            name=name,
            description=description,
            version=version,
            created_by=user_id,
        )
        workflow = self.workflow_repo.create(workflow)

        # Build nodes
        node_id_map = {}
        for idx, node_info in enumerate(nodes):
            node = WorkflowNode(
                workflow_id=workflow.id,
                node_type=node_info["node_type"],
                name=node_info["name"],
                configuration=node_info.get("configuration", {}),
                timeout=node_info.get("timeout", 60.0),
            )
            node = self.db.merge(node)
            self.db.add(node)
            self.db.flush()
            node_id_map[idx] = node.id

        # Build edges
        for edge_info in edges:
            edge = WorkflowEdge(
                workflow_id=workflow.id,
                source_node_id=node_id_map[edge_info["source_node_index"]],
                target_node_id=node_id_map[edge_info["target_node_index"]],
                transition_condition=edge_info.get("transition_condition"),
                priority=edge_info.get("priority", 0),
            )
            self.db.add(edge)

        self.db.commit()
        return workflow

    def get_workflow(self, org_id: int, workflow_id: int) -> Workflow | None:
        """Get workflow details."""
        return self.workflow_repo.get_by_org_and_id(org_id, workflow_id)

    def get_execution(self, org_id: int, execution_id: int) -> WorkflowExecution | None:
        """Get execution details."""
        return self.execution_repo.get_by_org_and_id(org_id, execution_id)

    async def execute_workflow(
        self,
        workflow_id: int,
        organization_id: int,
        agent_id: int,
        current_user: User,
    ) -> WorkflowExecution:
        """
        Runs the full workflow execution pipeline loop:
          1. Validation checks
          2. Entry initialization
          3. Node executor routing
          4. Transition evaluations
          5. State writes
        """
        workflow = self.workflow_repo.get_by_org_and_id(organization_id, workflow_id)
        if not workflow:
            raise ValueError("Workflow not found.")

        # Graph check
        self.validator.validate_graph(workflow)

        # Initialize execution tracking record
        execution = WorkflowExecution(
            workflow_id=workflow_id,
            organization_id=organization_id,
            agent_id=agent_id,
            status="RUNNING",
            execution_context={"variables": {"status": "pending"}},
        )
        execution = self.execution_repo.create(execution)

        # Run nodes sequentially starting from 'Start'
        nodes = workflow.nodes
        edges = workflow.edges
        current_node = next((n for n in nodes if n.node_type.lower() == "start"), None)

        start_time = time.perf_counter()
        while current_node:
            execution.current_node_id = current_node.id
            self.execution_repo.update(execution)

            step_started = datetime.now(timezone.utc)
            node_output: dict[str, Any] = {}
            status = "COMPLETED"
            error_message = None
            retries_used = 0
            try:
                node_output, retries_used = await self._execute_node(
                    current_node,
                    execution,
                    organization_id,
                    agent_id,
                    current_user,
                )
                execution.execution_context = self._merge_execution_context(
                    execution.execution_context,
                    current_node,
                    node_output,
                )
            except Exception as exc:
                status = "FAILED"
                error_message = str(exc)
                execution.execution_context = self._merge_execution_context(
                    execution.execution_context,
                    current_node,
                    {"success": False, "error": error_message},
                )

            # Record step execution audit log
            step = WorkflowStep(
                execution_id=execution.id,
                node_id=current_node.id,
                status=status,
                input_data=current_node.configuration or {},
                output_data=node_output,
                retries=retries_used,
                error_message=error_message,
                started_at=step_started,
                completed_at=datetime.now(timezone.utc),
                latency_seconds=(datetime.now(timezone.utc) - step_started).total_seconds(),
            )
            self.db.add(step)
            self.db.commit()

            if status == "FAILED":
                execution.status = "FAILED"
                execution.completed_at = datetime.now(timezone.utc)
                execution.duration = time.perf_counter() - start_time
                self.execution_repo.update(execution)
                return execution

            if current_node.node_type.lower() == "end":
                break

            # Find conditional edge matching transition conditions
            matching_edges = [e for e in edges if e.source_node_id == current_node.id]
            next_node_id = self.transition_engine.evaluate_transition(
                matching_edges,
                execution.execution_context,
            )
            current_node = next((n for n in nodes if n.id == next_node_id), None) if next_node_id else None

        execution.status = "COMPLETED"
        execution.completed_at = datetime.now(timezone.utc)
        execution.duration = time.perf_counter() - start_time
        self.execution_repo.update(execution)

        return execution

    async def _execute_node(
        self,
        node: WorkflowNode,
        execution: WorkflowExecution,
        organization_id: int,
        agent_id: int,
        current_user: User,
    ) -> tuple[dict[str, Any], int]:
        config = node.configuration or {}
        node_type = node.node_type.lower()
        attempts = int((node.retry_policy or {}).get("max_retries", 0)) + 1
        last_error: Exception | None = None

        for attempt in range(attempts):
            try:
                if node_type in {"start", "end"}:
                    return {"success": True, "node_type": node_type}, attempt
                if node_type in {"memory", "memory_search"}:
                    service = MemoryService(self.db)
                    memories = await service.retrieve_memories(
                        org_id=organization_id,
                        agent_id=agent_id,
                        query=config.get("query") or execution.execution_context.get("objective", ""),
                        top_k=config.get("top_k", 5),
                    )
                    return {
                        "success": True,
                        "memories": [
                            {"id": memory.id, "title": memory.title, "content": memory.content}
                            for memory in memories
                        ],
                    }, attempt
                if node_type in {"rag", "knowledge", "knowledge_search"}:
                    kb_id = config.get("kb_id") or config.get("knowledge_base_id")
                    if kb_id is None:
                        return {"success": False, "placeholder": True, "reason": "RAG node requires kb_id in configuration."}, attempt
                    context = await RAGService(self.db).retrieve_context(
                        kb_id=kb_id,
                        query=config.get("query") or execution.execution_context.get("objective", ""),
                        top_k=config.get("top_k", 5),
                        max_tokens=config.get("max_tokens", 2000),
                    )
                    return {"success": True, "context": context}, attempt
                if node_type in {"tool", "tool_call", "execute_tool"}:
                    tool_name = config.get("tool_name") or config.get("name")
                    if not tool_name:
                        return {"success": False, "placeholder": True, "reason": "Tool node requires tool_name in configuration."}, attempt
                    result = await ToolExecutionService(self.db).execute_batch(
                        requests=[
                            ToolCallRequest(
                                call_id=str(config.get("call_id") or f"workflow-{execution.id}-{node.id}"),
                                tool_name=tool_name,
                                arguments=config.get("arguments", {}),
                            )
                        ],
                        current_user=current_user,
                        organization_id=organization_id,
                        agent_id=agent_id,
                        conversation_id=execution.conversation_id or 0,
                    )
                    return {"success": result.all_succeeded, "tool_results": [r.model_dump() for r in result.results]}, attempt
                return {"success": True, "placeholder": True, "reason": f"No executable runtime is registered for node type '{node.node_type}'."}, attempt
            except Exception as exc:
                last_error = exc
                if attempt == attempts - 1:
                    raise

        raise last_error or RuntimeError("Workflow node execution failed.")

    def _merge_execution_context(
        self,
        context: dict[str, Any] | None,
        node: WorkflowNode,
        output: dict[str, Any],
    ) -> dict[str, Any]:
        updated = dict(context or {})
        variables = dict(updated.get("variables") or {})
        variables["status"] = "completed" if output.get("success") else "failed"
        variables[node.name] = output
        updated["variables"] = variables
        updated.setdefault("node_history", []).append(
            {"node_id": node.id, "node_name": node.name, "node_type": node.node_type, "output": output}
        )
        return updated

    def pause_execution(self, org_id: int, execution_id: int) -> WorkflowExecution:
        """Pause a running workflow."""
        execution = self.get_execution(org_id, execution_id)
        if not execution:
            raise ValueError("Execution not found.")
        execution.status = "PAUSED"
        return self.execution_repo.update(execution)

    def resume_execution(self, org_id: int, execution_id: int) -> WorkflowExecution:
        """Resume a paused workflow."""
        execution = self.get_execution(org_id, execution_id)
        if not execution:
            raise ValueError("Execution not found.")
        execution.status = "RUNNING"
        return self.execution_repo.update(execution)

    def cancel_execution(self, org_id: int, execution_id: int) -> WorkflowExecution:
        """Cancel a running workflow."""
        execution = self.get_execution(org_id, execution_id)
        if not execution:
            raise ValueError("Execution not found.")
        execution.status = "CANCELLED"
        execution.completed_at = datetime.now(timezone.utc)
        return self.execution_repo.update(execution)
