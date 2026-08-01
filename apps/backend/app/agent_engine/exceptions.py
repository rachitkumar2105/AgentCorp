"""
Agent Engine — Exceptions.
"""

from __future__ import annotations


class AgentEngineError(Exception):
    """Base exception for all agent engine failures."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class GoalValidationError(AgentEngineError):
    """Raised when goal parameters fail schema validation checks."""


class AgentExecutionError(AgentEngineError):
    """Raised when execution tracking encounters errors."""
