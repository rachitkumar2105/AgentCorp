"""
Memory Engine — Exceptions.
"""

from __future__ import annotations


class MemoryEngineError(Exception):
    """Base exception for all memory engine failures."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class MemoryNotFoundError(MemoryEngineError):
    """Raised when memory entry doesn't exist."""


class MemoryValidationError(MemoryEngineError):
    """Raised when validation parsing fails."""
