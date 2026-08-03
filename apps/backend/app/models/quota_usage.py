"""app/models/quota_usage.py

SQLAlchemy model for tracking quota usage per entity (user or organization).

Fields:
  - entity_id: user_id or organization_id
  - quota_type: logical quota name (e.g., "ai_tokens", "api_calls")
  - used: units consumed in the current period
  - limit: maximum allowed units per period
  - period_start: when the current measurement window began
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, Integer, String

from app.db.base import Base


class QuotaUsage(Base):
    __tablename__ = "quota_usage"

    id = Column(Integer, primary_key=True, index=True)
    entity_id = Column(Integer, nullable=False, index=True)  # user_id or org_id
    quota_type = Column(String(64), nullable=False, index=True)  # e.g. "ai_tokens"
    used = Column(BigInteger, default=0, nullable=False)
    limit = Column(BigInteger, nullable=True)  # None → use DEFAULT_AI_TOKENS_QUOTA
    period_start = Column(DateTime, default=datetime.utcnow, nullable=False)

    def reset(self) -> None:
        """Reset usage to zero and start a new period."""
        self.used = 0
        self.period_start = datetime.utcnow()

    @property
    def remaining(self) -> int | None:
        if self.limit is None:
            return None
        return max(0, self.limit - self.used)

    @property
    def is_exceeded(self) -> bool:
        if self.limit is None:
            return False
        return self.used > self.limit
