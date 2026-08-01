"""
Knowledge Base Management System — Metadata extractor.
"""

from __future__ import annotations

from typing import Any


class MetadataExtractor:
    """
    Extracts core structured metadata fields.
    """

    def extract_metadata(
        self,
        filename: str,
        text: str,
        raw_metadata: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Produce a unified structured JSON metadata block.
        """
        # basic extraction logic
        return {
            "title": filename.rsplit(".", 1)[0],
            "file_name": filename,
            "character_count": len(text),
            "word_count": len(text.split()),
            **raw_metadata,
        }
