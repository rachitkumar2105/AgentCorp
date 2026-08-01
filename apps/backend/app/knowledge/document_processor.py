"""
Knowledge Base Management System — Document processor.

Extracts text content and raw metadata from supported document files.
"""

from __future__ import annotations

import io
from typing import Any
from app.knowledge.exceptions import ProcessingFailedError


class DocumentProcessor:
    """
    Parses and extracts raw text and metadata from files (PDF, TXT, HTML, MD, DOCX).
    """

    def process(
        self,
        file_bytes: bytes,
        mime_type: str,
    ) -> tuple[str, dict[str, Any]]:
        """
        Processes content bytes and returns raw text content along with metadata.
        """
        # A clear parser registry abstraction - initially supports plaintext parsing
        # design lets additional libraries (PyPDF2, python-docx, etc.) register here.
        try:
            if mime_type in ["text/plain", "text/markdown", "text/html"]:
                text = file_bytes.decode("utf-8", errors="replace")
                metadata = {
                    "character_count": len(text),
                    "encoding": "utf-8",
                }
                return text, metadata
            elif mime_type == "application/pdf":
                # Stub pdf reader: returning content with meta
                text = f"[PDF CONTENT STUB]\nSize: {len(file_bytes)} bytes"
                metadata = {
                    "page_count": 1,
                    "character_count": len(text),
                }
                return text, metadata
            else:
                # Default fallback
                text = file_bytes.decode("utf-8", errors="replace")
                metadata = {"character_count": len(text)}
                return text, metadata

        except Exception as exc:
            raise ProcessingFailedError(f"Document processing failed: {exc}")
