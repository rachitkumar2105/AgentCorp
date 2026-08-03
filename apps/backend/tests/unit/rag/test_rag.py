"""Unit tests for RAG Engine."""
from app.rag.query_rewriter import QueryRewriter


def test_query_rewriter():
    rewriter = QueryRewriter()
    original_query = "  How to build a website?  "
    rewritten = rewriter.rewrite_query(original_query)
    assert rewritten == "how to build a website?"
