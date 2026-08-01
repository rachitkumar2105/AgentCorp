"""
Dependencies for the observability framework.
"""

from typing import Annotated
from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.audit_repository import AuditRepository
from app.repositories.metric_repository import MetricRepository, OperationLogRepository
from app.services.audit_log_service import AuditLogService
from app.services.observability_service import ObservabilityService


def get_audit_repository(db: Session = Depends(get_db)) -> AuditRepository:
    return AuditRepository(db)


def get_metric_repository(db: Session = Depends(get_db)) -> MetricRepository:
    return MetricRepository(db)


def get_operation_log_repository(db: Session = Depends(get_db)) -> OperationLogRepository:
    return OperationLogRepository(db)


def get_audit_log_service(
    repo: AuditRepository = Depends(get_audit_repository)
) -> AuditLogService:
    return AuditLogService(repo)


def get_observability_service(
    metric_repo: MetricRepository = Depends(get_metric_repository),
    op_log_repo: OperationLogRepository = Depends(get_operation_log_repository),
) -> ObservabilityService:
    return ObservabilityService(metric_repo, op_log_repo)


AuditLogServiceDependency = Annotated[AuditLogService, Depends(get_audit_log_service)]
ObservabilityServiceDependency = Annotated[ObservabilityService, Depends(get_observability_service)]
