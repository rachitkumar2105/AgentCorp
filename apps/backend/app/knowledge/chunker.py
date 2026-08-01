"""
Knowledge Base Management System — Chunker.

Splits large document text blocks into semantic chunks with overlap.
"""

from __future__ import annotations

import re


class Chunker:
    """
    Semantic text chunker.
    """

    def chunk_text(
        self,
        text: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> list[dict[str, Any]]:
        """
        Splits text into chunks, preserving semantic boundaries where possible.
        """
        # A simple character-based semantic splitting implementation
        # Splits on double newlines (paragraphs) first
        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = []
        current_size = 0

        for para in paragraphs:
            para_len = len(para)
            if current_size + para_len > chunk_size and current_chunk:
                # Merge current chunk
                chunk_txt = "\n\n".join(current_chunk)
                chunks.append({
                    "text": chunk_txt,
                    "character_count": len(chunk_txt),
                    # Token count approximation
                    "token_count": int(len(chunk_txt) / 4),
                })
                # Retain overlap items if possible
                current_chunk = current_chunk[-1:] if len(current_chunk) > 1 else current_chunk
                current_size = sum(len(p) for p in current_chunk)

            current_chunk.append(para)
            current_size += para_len

        # Append final chunk
        if current_chunk:
            chunk_txt = "\n\n".join(current_chunk)
            chunks.append({
                "text": chunk_txt,
                "character_count": len(chunk_txt),
                "token_count": int(len(chunk_txt) / 4),
            })

        return chunks
