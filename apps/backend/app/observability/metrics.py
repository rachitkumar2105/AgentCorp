"""
Metrics collection abstraction.
Supports future Prometheus, Grafana, Datadog, etc.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from app.observability.logging import get_logger

logger = get_logger(__name__)


class MetricBackend(ABC):
    """Abstract base class for metrics storage/exporters."""

    @abstractmethod
    async def record_counter(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None) -> None:
        """Record increment to a counter metric."""
        pass

    @abstractmethod
    async def record_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Record value of a gauge metric."""
        pass

    @abstractmethod
    async def record_histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Record value of a histogram (distribution) metric."""
        pass


class InMemoryMetricBackend(MetricBackend):
    """In-memory thread-safe metric backend implementation for local storage/dashboard query."""

    def __init__(self):
        self.counters: Dict[str, Dict[str, int]] = {}
        self.gauges: Dict[str, Dict[str, float]] = {}
        self.histograms: Dict[str, List[Dict[str, Any]]] = {}
        self._lock = asyncio.Lock()

    def _get_tag_string(self, tags: Optional[Dict[str, str]]) -> str:
        if not tags:
            return ""
        return ",".join(f"{k}={v}" for k, v in sorted(tags.items()))

    async def record_counter(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None) -> None:
        async with self._lock:
            tag_str = self._get_tag_string(tags)
            if name not in self.counters:
                self.counters[name] = {}
            self.counters[name][tag_str] = self.counters[name].get(tag_str, 0) + value

    async def record_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        async with self._lock:
            tag_str = self._get_tag_string(tags)
            if name not in self.gauges:
                self.gauges[name] = {}
            self.gauges[name][tag_str] = value

    async def record_histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        async with self._lock:
            if name not in self.histograms:
                self.histograms[name] = []
            self.histograms[name].append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "value": value,
                "tags": tags or {}
            })

    async def get_metrics_snapshot(self) -> Dict[str, Any]:
        """Return snapshot of current metrics."""
        async with self._lock:
            return {
                "counters": dict(self.counters),
                "gauges": dict(self.gauges),
                "histograms": {k: list(v) for k, v in self.histograms.items()}
            }


class MetricsRegistry:
    """Registry class wrapping the active backend."""

    def __init__(self, backend: MetricBackend):
        self.backend = backend

    async def increment(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None) -> None:
        try:
            await self.backend.record_counter(name, value, tags)
        except Exception as e:
            logger.error("Failed to record counter %s: %s", name, str(e))

    async def gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        try:
            await self.backend.record_gauge(name, value, tags)
        except Exception as e:
            logger.error("Failed to record gauge %s: %s", name, str(e))

    async def histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        try:
            await self.backend.record_histogram(name, value, tags)
        except Exception as e:
            logger.error("Failed to record histogram %s: %s", name, str(e))


# Global metrics registry instanced with InMemoryBackend
backend_instance = InMemoryMetricBackend()
metrics = MetricsRegistry(backend_instance)
