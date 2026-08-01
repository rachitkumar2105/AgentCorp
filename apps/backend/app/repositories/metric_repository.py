"""
Metric repository implementation.
"""

from typing import List
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.system_metric import SystemMetric
from app.models.operation_log import OperationLog
from app.repositories.base_repository import BaseRepository


class MetricRepository(BaseRepository[SystemMetric]):
    """
    Repository for persisting and querying system metrics.
    """

    def __init__(self, db: Session):
        super().__init__(SystemMetric, db)

    def get_latest_metrics(self, limit: int = 100) -> List[SystemMetric]:
        """Query recent system metric records."""
        statement = select(self.model).order_by(self.model.created_at.desc()).limit(limit)
        return list(self.db.scalars(statement).all())


class OperationLogRepository(BaseRepository[OperationLog]):
    """
    Repository for persisting execution trace spans.
    """

    def __init__(self, db: Session):
        super().__init__(OperationLog, db)
