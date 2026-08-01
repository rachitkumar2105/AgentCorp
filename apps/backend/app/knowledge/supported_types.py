"""
Knowledge Base Management System — Supported file types.
"""

from __future__ import annotations

SUPPORTED_MIME_TYPES = {
    "application/pdf": "pdf",
    "text/plain": "txt",
    "text/markdown": "md",
    "text/html": "html",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
}


def is_supported_mime_type(mime_type: str) -> bool:
    """Return True if the mime type is supported."""
    return mime_type in SUPPORTED_MIME_TYPES
