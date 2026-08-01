"""
RAG Engine — Reranker.
"""

from __future__ import annotations


class ReRanker:
    """
    Reranker abstraction.
    Initially implements the identity reranker (no changes to ranking).
    """

    def rerank(
        self,
        ranked_items: list[tuple[int, float]],
    ) -> list[tuple[int, float]]:
        """Placeholder for Jina / Cohere. Currently leaves ordering intact."""
        return ranked_items
