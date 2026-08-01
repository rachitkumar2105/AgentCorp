"""
Workflow Engine — Exceptions.
"""

from __future__ import annotations


class WorkflowEngineError(Exception):
    """Base exception for all workflow failures."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class WorkflowValidationError(WorkflowEngineError):
    """Raised when graph validation fails."""


class WorkflowExecutionError(WorkflowEngineError):
    """Raised during runtime node failures."""
