"""
RAG Engine — Chunk Selector.
"""

from __future__ import annotations


class ChunkSelector:
    """
    Clamps selected chunks to context budget tokens or list sizes.
    """

    def select_chunks(
        self,
        ranked_items: list[tuple[int, float]],
        max_chunks: int = 5,
        max_tokens: int = 2000,
    ) -> list[int]:
        """Clamps the results to fit context budget constraints."""
        selected = []
        token_count = 0
        for chunk_id, _ in ranked_items[:max_chunks]:
            # Approximate cost
            token_count += 200
            if token_count > max_tokens:
                break
            selected.append(chunk_id)
        return selected
