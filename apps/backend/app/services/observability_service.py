"""
Observability and dashboard operations service.
"""

from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.observability.health import check_dependency_health
from app.observability.diagnostics import get_diagnostics_snapshot
from app.observability.metrics import backend_instance
from app.observability.tracing import tracer
from app.repositories.metric_repository import MetricRepository, OperationLogRepository
from app.services.base_service import BaseService


class ObservabilityService(BaseService[MetricRepository]):
    """
    Main aggregator service for system observability.
    Queries metrics, traces, active diagnostics, and dependency status.
    """

    def __init__(self, repository: MetricRepository, operation_log_repo: OperationLogRepository):
        super().__init__(repository)
        self.operation_log_repo = operation_log_repo

    async def get_health_status(self) -> Dict[str, Any]:
        """Verify health of dependencies."""
        return await check_dependency_health()

    async def get_diagnostics(self) -> Dict[str, Any]:
        """Fetch current diagnostics snapshot."""
        return await get_diagnostics_snapshot()

    async def get_metrics_dashboard(self) -> Dict[str, Any]:
        """Fetch system-wide metric values snapshot."""
        return await backend_instance.get_metrics_snapshot()

    async def get_active_traces(self) -> List[Dict[str, Any]]:
        """Fetch trace spans recorded."""
        return tracer.finished_spans
