"""
Tool Execution Service.

Coordinates database persistence, auditing, caching, and discovery mappings.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.agent_tool_repository import AgentToolRepository
from app.repositories.tool_repository import ToolRepository
from app.schemas.tool_execution import (
    ToolCallRequest,
    ToolCallResult,
    ToolExecutionResult,
    ToolMetadata,
    ToolSchema,
    ToolParameter,
)
from app.tools.dispatcher import ToolDispatcher
from app.tools.executor import ToolExecutor
from app.tools.registry import tool_registry
from app.tools.validator import ToolValidator

logger = logging.getLogger("tool_execution_service")


class ToolExecutionService:
    """
    Coordinates tool discovery, verification, and audit trail persistence.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.tool_repo = ToolRepository(db)
        self.agent_tool_repo = AgentToolRepository(db)

        # Wire dispatcher dependencies
        validator = ToolValidator(self.tool_repo, self.agent_tool_repo)
        executor = ToolExecutor()
        self.dispatcher = ToolDispatcher(validator, executor)

    def discover_agent_tools(
        self,
        agent_id: int,
        organization_id: int,
        current_user: User,
    ) -> list[ToolMetadata]:
        """
        Discover and return all tool metadata assigned to the agent.
        """
        # Fetch assignments from database
        assignments = self.agent_tool_repo.get_by_agent(agent_id)
        tools_meta: list[ToolMetadata] = []

        for assignment in assignments:
            db_tool = self.tool_repo.get(assignment.tool_id)
            if not db_tool:
                continue

            # Verify in registry
            if tool_registry.is_registered(db_tool.name):
                # Sync ID mapping
                tool_registry.sync_db_id(db_tool.name, db_tool.id)
                meta = tool_registry.get_metadata(db_tool.name)
                tools_meta.append(meta)

        return tools_meta

    async def execute_batch(
        self,
        requests: list[ToolCallRequest],
        current_user: User,
        organization_id: int,
        agent_id: int,
        conversation_id: int,
    ) -> ToolExecutionResult:
        """
        Execute multiple tool call requests sequentially.
        """
        start_time = time.perf_counter()
        results: list[ToolCallResult] = []
        all_succeeded = True

        for req in requests:
            # Inject context
            req.agent_id = agent_id
            req.organization_id = organization_id
            req.conversation_id = conversation_id

            res = await self.dispatcher.dispatch(req, current_user)
            results.append(res)
            if not res.success:
                all_succeeded = False

            # Persist execution audit log (placeholder - will map to Alembic table log)
            self._log_audit(req, res, agent_id, organization_id, conversation_id)

        latency = time.perf_counter() - start_time
        return ToolExecutionResult(
            results=results,
            total_latency_seconds=latency,
            all_succeeded=all_succeeded,
        )

    def _log_audit(
        self,
        req: ToolCallRequest,
        res: ToolCallResult,
        agent_id: int,
        organization_id: int,
        conversation_id: int,
    ) -> None:
        """
        Persist execution telemetry for billing and auditing.
        """
        logger.info(
            "tool_audit | tool=%s success=%s latency=%.4fs org=%s conv=%s agent=%s",
            req.tool_name,
            res.success,
            res.latency_seconds,
            organization_id,
            conversation_id,
            agent_id,
        )
