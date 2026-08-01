"""
RAG Engine — Exceptions.
"""

from __future__ import annotations


class RAGEngineError(Exception):
    """Base exception for all RAG engine errors."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class EmbeddingGenerationError(RAGEngineError):
    """Raised when generating vector embeddings fails."""


class VectorStoreError(RAGEngineError):
    """Raised when vector store operations fail."""


class RerankingError(RAGEngineError):
    """Raised when re-ranking operations fail."""
