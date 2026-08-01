"""
Observability API endpoints.
"""

from typing import Any, Dict, List
from fastapi import APIRouter, Depends, Query

from app.dependencies.auth import get_current_active_user
from app.dependencies.permissions import RequirePermission
from app.dependencies.observability import ObservabilityServiceDependency, AuditLogServiceDependency
from app.models.user import User
from app.schemas.observability import DiagnosticsResponse, MetricsSnapshot
from app.schemas.audit_log import AuditLogOut

# Router definition
router = APIRouter(
    tags=["Observability"],
)


@router.get(
    "/operations/metrics",
    response_model=MetricsSnapshot,
    dependencies=[Depends(RequirePermission("operations:read"))],
)
async def get_system_metrics(
    service: ObservabilityServiceDependency,
) -> Any:
    """
    Fetch current snapshot of system metrics.
    """
    return await service.get_metrics_dashboard()


@router.get(
    "/operations/providers",
    dependencies=[Depends(RequirePermission("operations:read"))],
)
async def get_provider_metrics(
    service: ObservabilityServiceDependency,
) -> Any:
    """
    Fetch AI Provider operational metrics.
    """
    metrics = await service.get_metrics_dashboard()
    # Filter or aggregate provider specific counter/gauge/histogram data
    # Let's extract any keys starting with provider_
    counters = {k: v for k, v in metrics.get("counters", {}).items() if "provider" in k}
    histograms = {k: v for k, v in metrics.get("histograms", {}).items() if "provider" in k}
    return {"counters": counters, "histograms": histograms}


@router.get(
    "/operations/executions",
    response_model=DiagnosticsResponse,
    dependencies=[Depends(RequirePermission("operations:read"))],
)
async def get_active_executions(
    service: ObservabilityServiceDependency,
) -> Any:
    """
    Fetch active executions and system runs.
    """
    return await service.get_diagnostics()


@router.get(
    "/operations/streams",
    dependencies=[Depends(RequirePermission("operations:read"))],
)
async def get_active_streams(
    service: ObservabilityServiceDependency,
) -> Any:
    """
    Fetch active streaming requests.
    """
    diagnostics = await service.get_diagnostics()
    return {
        "active_streams_count": diagnostics["active_streams_count"],
        "active_streams": diagnostics["active_streams"],
    }


@router.get(
    "/operations/workflows",
    dependencies=[Depends(RequirePermission("operations:read"))],
)
async def get_active_workflows(
    service: ObservabilityServiceDependency,
) -> Any:
    """
    Fetch active workflow executions.
    """
    diagnostics = await service.get_diagnostics()
    return {
        "active_workflows_count": diagnostics["active_workflows_count"],
        "active_workflows": diagnostics["active_workflows"],
    }


@router.get(
    "/operations/multi-agent",
    dependencies=[Depends(RequirePermission("operations:read"))],
)
async def get_active_multi_agent_sessions(
    service: ObservabilityServiceDependency,
) -> Any:
    """
    Fetch active multi-agent sessions.
    """
    diagnostics = await service.get_diagnostics()
    return {
        "active_sessions_count": diagnostics["active_sessions_count"],
        "active_sessions": diagnostics["active_sessions"],
    }


@router.get(
    "/audit",
    response_model=List[AuditLogOut],
    dependencies=[Depends(RequirePermission("audit:read"))],
)
async def get_audit_logs(
    audit_service: AuditLogServiceDependency,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    organization_id: int | None = Query(None),
) -> Any:
    """
    Retrieve paginated audit logs. RBAC protected.
    """
    return audit_service.get_audit_logs(skip=skip, limit=limit, organization_id=organization_id)
