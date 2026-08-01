"""
Memory Engine — Summarizer.
"""

from __future__ import annotations


class Summarizer:
    """
    Condenses long dialogue flows to prevent LLM context overflows.
    """

    def summarize(self, text: str) -> str:
        """Produce compressed dialogue state summaries."""
        # Simple character count compression stub
        words = text.split()
        summary_content = " ".join(words[:min(len(words), 50)])
        return f"Summary of conversation: {summary_content}..."
