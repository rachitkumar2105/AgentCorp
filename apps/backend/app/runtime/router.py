"""
Version-aware runtime router.
"""

from __future__ import annotations

import asyncio
from dataclasses import asdict
import uuid
from enum import Enum
from typing import AsyncGenerator, Any

from app.observability.diagnostics import register_execution, unregister_execution
from app.observability.diagnostics import register_cognitive_analysis, unregister_cognitive_analysis
from app.observability.diagnostics import register_planning_run, unregister_planning_run
from app.observability.tracing import tracer
from app.runtime.contract import RuntimeContract


class RuntimeVersion(str, Enum):
    V1 = "AgentCorp V1"
    V2 = "AgentCorp V2"


class RuntimeRouter:
    """
    Single entrypoint for AI runtime selection.
    """

    def __init__(self, v1_runtime: RuntimeContract, v2_runtime: RuntimeContract) -> None:
        self._runtimes = {
            RuntimeVersion.V1.value: v1_runtime,
            RuntimeVersion.V2.value: v2_runtime,
        }

    def resolve(self, runtime_version: str | None) -> RuntimeContract:
        return self._runtimes.get(runtime_version or RuntimeVersion.V1.value, self._runtimes[RuntimeVersion.V1.value])

    async def execute_chat(self, *args: Any, runtime_version: str | None = None, **kwargs: Any) -> Any:
        runtime = self.resolve(runtime_version)
        execution_id = str(uuid.uuid4())
        await register_execution(execution_id, {
            "execution_id": execution_id,
            "runtime_version": runtime_version or RuntimeVersion.V1.value,
            "stage": "chat",
            "status": "RUNNING",
        })
        with tracer.start_span("runtime_router.chat", {"runtime_version": runtime_version or RuntimeVersion.V1.value}):
            try:
                if hasattr(runtime, "analyze_request") and kwargs.get("payload") is not None:
                    analysis_id = str(uuid.uuid4())
                    planning_id = str(uuid.uuid4())
                    payload = kwargs["payload"]
                    await register_cognitive_analysis(
                        analysis_id,
                        {
                            "analysis_id": analysis_id,
                            "runtime_version": runtime_version or RuntimeVersion.V1.value,
                            "request_text": getattr(payload, "message", None),
                            "stage": "cognitive_understanding",
                            "status": "RUNNING",
                        },
                    )
                    try:
                        cognitive_state = runtime.analyze_request(
                            request_text=getattr(payload, "message", ""),
                            runtime_version=runtime_version or RuntimeVersion.V1.value,
                            request_id=execution_id,
                        )
                        await register_cognitive_analysis(
                            analysis_id,
                            {
                                "analysis_id": analysis_id,
                                "runtime_version": runtime_version or RuntimeVersion.V1.value,
                                "stage": "cognitive_understanding",
                                "status": "COMPLETED",
                                "cognitive_state": asdict(cognitive_state),
                            },
                        )
                        if hasattr(runtime, "plan_request"):
                            execution_blueprint = runtime.plan_request(
                                cognitive_state=cognitive_state,
                                runtime_version=runtime_version or RuntimeVersion.V1.value,
                                request_id=execution_id,
                            )
                            await register_planning_run(
                                planning_id,
                                {
                                    "planning_id": planning_id,
                                    "runtime_version": runtime_version or RuntimeVersion.V1.value,
                                    "stage": "strategic_planning",
                                    "status": "COMPLETED",
                                    "execution_blueprint": asdict(execution_blueprint),
                                },
                            )
                    finally:
                        await unregister_cognitive_analysis(analysis_id)
                        await unregister_planning_run(planning_id)
                result = await runtime.execute_chat(*args, **kwargs)
                await register_execution(execution_id, {
                    "execution_id": execution_id,
                    "runtime_version": runtime_version or RuntimeVersion.V1.value,
                    "stage": "chat",
                    "status": "COMPLETED",
                })
                return result
            finally:
                await unregister_execution(execution_id)

    async def execute_stream(self, *args: Any, runtime_version: str | None = None, **kwargs: Any) -> AsyncGenerator[str, None]:
        runtime = self.resolve(runtime_version)
        async for chunk in runtime.execute_stream(*args, **kwargs):
            yield chunk

    async def execute_agent(self, *args: Any, runtime_version: str | None = None, **kwargs: Any) -> Any:
        runtime = self.resolve(runtime_version)
        return await runtime.execute_agent(*args, **kwargs)

    async def execute_workflow(self, *args: Any, runtime_version: str | None = None, **kwargs: Any) -> Any:
        runtime = self.resolve(runtime_version)
        return await runtime.execute_workflow(*args, **kwargs)

    async def execute_tools(self, *args: Any, runtime_version: str | None = None, **kwargs: Any) -> Any:
        runtime = self.resolve(runtime_version)
        return await runtime.execute_tools(*args, **kwargs)
