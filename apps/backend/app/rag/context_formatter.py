"""
RAG Engine — Context Formatter.
"""

from __future__ import annotations


class ContextFormatter:
    """
    Serializes retrieved chunk contents into standard prompt context.
    """

    def format_context(self, chunks: list[dict[str, Any]]) -> str:
        """Merge text segments cleanly."""
        blocks = []
        for chunk in chunks:
            blocks.append(
                f"Source Document: {chunk.get('document_name')}\n"
                f"Content: {chunk.get('text')}\n"
            )
        return "\n---\n".join(blocks)
