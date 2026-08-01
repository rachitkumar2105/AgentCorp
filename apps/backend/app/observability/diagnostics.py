"""
Diagnostics service for tracking active executions, sessions, and streams.
"""

import asyncio
from typing import Dict, Any, List

# Thread-safe in-memory maps for live tracking
active_executions: Dict[str, Dict[str, Any]] = {}
active_streams: Dict[str, Dict[str, Any]] = {}
active_sessions: Dict[str, Dict[str, Any]] = {}
active_workflows: Dict[str, Dict[str, Any]] = {}

_lock = asyncio.Lock()


async def register_execution(execution_id: str, metadata: Dict[str, Any]) -> None:
    async with _lock:
        active_executions[execution_id] = metadata


async def unregister_execution(execution_id: str) -> None:
    async with _lock:
        active_executions.pop(execution_id, None)


async def register_stream(stream_id: str, metadata: Dict[str, Any]) -> None:
    async with _lock:
        active_streams[stream_id] = metadata


async def unregister_stream(stream_id: str) -> None:
    async with _lock:
        active_streams.pop(stream_id, None)


async def register_session(session_id: str, metadata: Dict[str, Any]) -> None:
    async with _lock:
        active_sessions[session_id] = metadata


async def unregister_session(session_id: str) -> None:
    async with _lock:
        active_sessions.pop(session_id, None)


async def register_workflow(workflow_id: str, metadata: Dict[str, Any]) -> None:
    async with _lock:
        active_workflows[workflow_id] = metadata


async def unregister_workflow(workflow_id: str) -> None:
    async with _lock:
        active_workflows.pop(workflow_id, None)


async def get_diagnostics_snapshot() -> Dict[str, Any]:
    async with _lock:
        return {
            "active_executions_count": len(active_executions),
            "active_executions": list(active_executions.values()),
            "active_streams_count": len(active_streams),
            "active_streams": list(active_streams.values()),
            "active_sessions_count": len(active_sessions),
            "active_sessions": list(active_sessions.values()),
            "active_workflows_count": len(active_workflows),
            "active_workflows": list(active_workflows.values()),
        }
