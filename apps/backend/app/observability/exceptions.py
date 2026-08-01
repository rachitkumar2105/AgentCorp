"""
Observability exceptions.
"""

class ObservabilityError(Exception):
    """Base exception for all observability related errors."""
    pass

class LoggingError(ObservabilityError):
    """Exception raised when structured logging fails."""
    pass

class MetricsError(ObservabilityError):
    """Exception raised when recording metrics fails."""
    pass

class TracingError(ObservabilityError):
    """Exception raised when trace span creation or management fails."""
    pass

class AuditError(ObservabilityError):
    """Exception raised when recording audit log entries fails."""
    pass
