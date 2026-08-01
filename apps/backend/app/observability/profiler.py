"""
Performance profiler and alerting interface.
"""

import time
from typing import Any, Dict, List, Optional
from app.observability.logging import get_logger
from app.observability.constants import (
    SLOW_REQUEST_THRESHOLD,
    SLOW_DATABASE_THRESHOLD,
    SLOW_PROVIDER_THRESHOLD,
    SLOW_WORKFLOW_THRESHOLD,
    SLOW_TOOL_THRESHOLD,
    SLOW_RAG_THRESHOLD,
    SLOW_MEMORY_THRESHOLD,
)

logger = get_logger(__name__)


# Alert Interface definition
class AlertBackend:
    """Interface for alerting hooks."""
    
    async def send_alert(self, title: str, message: str, severity: str = "warning", context: Optional[Dict[str, Any]] = None) -> None:
        """Send an alert to the configured backend."""
        pass


class ConsoleAlertBackend(AlertBackend):
    """Console implementation of AlertBackend."""
    
    async def send_alert(self, title: str, message: str, severity: str = "warning", context: Optional[Dict[str, Any]] = None) -> None:
        logger.warning(
            "ALERT [%s] - %s: %s | Context: %s",
            severity.upper(),
            title,
            message,
            context or {}
        )


class AlertManager:
    """Manages active alert backends and dispatches alerts."""
    
    def __init__(self):
        self._backends: List[AlertBackend] = [ConsoleAlertBackend()]

    def register_backend(self, backend: AlertBackend) -> None:
        self._backends.append(backend)

    async def trigger(self, title: str, message: str, severity: str = "warning", context: Optional[Dict[str, Any]] = None) -> None:
        for backend in self._backends:
            try:
                await backend.send_alert(title, message, severity, context)
            except Exception as e:
                logger.error("Failed to trigger alert: %s", str(e))


alert_manager = AlertManager()


class Profiler:
    """Context manager for profiling latency of individual blocks or subsystems."""

    THRESHOLD_MAP = {
        "request": SLOW_REQUEST_THRESHOLD,
        "database": SLOW_DATABASE_THRESHOLD,
        "provider": SLOW_PROVIDER_THRESHOLD,
        "workflow": SLOW_WORKFLOW_THRESHOLD,
        "tool": SLOW_TOOL_THRESHOLD,
        "rag": SLOW_RAG_THRESHOLD,
        "memory": SLOW_MEMORY_THRESHOLD,
    }

    def __init__(self, operation_type: str, operation_name: str, context: Optional[Dict[str, Any]] = None):
        self.operation_type = operation_type
        self.operation_name = operation_name
        self.context = context or {}
        self.start_time: float = 0.0
        self.duration: float = 0.0

    def __enter__(self) -> "Profiler":
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.duration = time.perf_counter() - self.start_time
        
        # Check slow operation threshold
        threshold = self.THRESHOLD_MAP.get(self.operation_type, 1.0)
        
        # Import metrics internally to avoid circular references
        from app.observability.metrics import metrics
        
        # Record metric duration
        import asyncio
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(metrics.histogram(
                f"{self.operation_type}_latency_seconds",
                self.duration,
                tags={"name": self.operation_name}
            ))

        if self.duration > threshold:
            msg = f"Operation '{self.operation_name}' ({self.operation_type}) took {self.duration:.4f}s (threshold: {threshold}s)"
            logger.warning(msg)
            
            # Send alert async if loop running
            if loop.is_running():
                loop.create_task(alert_manager.trigger(
                    title=f"Slow operation: {self.operation_name}",
                    message=msg,
                    severity="warning",
                    context={
                        "operation_type": self.operation_type,
                        "operation_name": self.operation_name,
                        "duration": self.duration,
                        "threshold": threshold,
                        **self.context
                    }
                ))
