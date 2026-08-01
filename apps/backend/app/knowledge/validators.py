"""
Knowledge Base Management System — Validators.

Performs document rules checks before processing.
"""

from __future__ import annotations

import hashlib
from app.knowledge.exceptions import FileValidationError, UnsupportedFileTypeError
from app.knowledge.supported_types import is_supported_mime_type

MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB upload ceiling


class DocumentValidator:
    """
    Validates uploaded document files against rules.
    """

    @staticmethod
    def validate_file(
        filename: str,
        content_type: str,
        file_size: int,
    ) -> None:
        """
        Validates content type, file size and naming.
        """
        # Validate MIME type
        if not is_supported_mime_type(content_type):
            raise UnsupportedFileTypeError(
                f"File content type '{content_type}' is not supported."
            )

        # Validate file size limits
        if file_size > MAX_FILE_SIZE_BYTES:
            raise FileValidationError(
                f"File size exceeds the limit of {MAX_FILE_SIZE_BYTES / (1024*1024):.1f} MB."
            )

        if not filename:
            raise FileValidationError("Filename cannot be empty.")

    @staticmethod
    def calculate_checksum(data: bytes) -> str:
        """Calculate SHA-256 checksum for byte streams."""
        return hashlib.sha256(data).hexdigest()
