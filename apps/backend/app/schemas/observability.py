"""
Observability response schemas.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class HealthDetail(BaseModel):
    status: str
    error: Optional[str] = None
    configured_providers: Optional[List[str]] = None


class HealthResponse(BaseModel):
    status: str
    details: Optional[Dict[str, Any]] = None


class MetricsSnapshot(BaseModel):
    counters: Dict[str, Dict[str, int]]
    gauges: Dict[str, Dict[str, float]]
    histograms: Dict[str, List[Dict[str, Any]]]


class ActiveExecutionInfo(BaseModel):
    execution_id: str
    metadata: Dict[str, Any]


class DiagnosticsResponse(BaseModel):
    active_executions_count: int
    active_executions: List[Dict[str, Any]]
    active_streams_count: int
    active_streams: List[Dict[str, Any]]
    active_sessions_count: int
    active_sessions: List[Dict[str, Any]]
    active_workflows_count: int
    active_workflows: List[Dict[str, Any]]
