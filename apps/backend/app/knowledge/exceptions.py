"""
Knowledge Base Management System — exceptions.
"""

from __future__ import annotations


class KnowledgeBaseError(Exception):
    """Base exception for all Knowledge Base errors."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class UnsupportedFileTypeError(KnowledgeBaseError):
    """Raised when the uploaded file type is not supported."""


class FileValidationError(KnowledgeBaseError):
    """Raised when document file verification fails."""


class DuplicateDocumentError(KnowledgeBaseError):
    """Raised when a duplicate document upload is detected."""


class ProcessingFailedError(KnowledgeBaseError):
    """Raised when the parsing or chunking processing pipeline fails."""
