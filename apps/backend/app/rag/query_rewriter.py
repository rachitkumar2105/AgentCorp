"""
RAG Engine — Query Rewriter.
"""

from __future__ import annotations


class QueryRewriter:
    """
    Cleans search terms to yield optimum vector query inputs.
    """

    def rewrite_query(self, query: str) -> str:
        """
        Normalize queries, remove noise.
        """
        return query.strip().lower()
