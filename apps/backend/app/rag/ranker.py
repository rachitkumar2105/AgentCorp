"""
RAG Engine — Ranker.
"""

from __future__ import annotations


class Ranker:
    """
    Ranks candidate chunks based on similarity scores.
    """

    def rank_candidates(
        self,
        candidates: list[tuple[int, float, dict]],
    ) -> list[tuple[int, float]]:
        """Sort candidates primarily by similarity score."""
        sorted_candidates = sorted(candidates, key=lambda x: x[1], reverse=True)
        return [(c[0], c[1]) for c in sorted_candidates]
