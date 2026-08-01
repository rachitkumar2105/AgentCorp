"""
RAG Engine — Vector Store Factory.
"""

from __future__ import annotations

from sqlalchemy.orm import Session
from app.rag.vector_store import BaseVectorStore
from app.rag.pgvector_store import PGVectorStore


class VectorStoreFactory:
    """
    Factory pattern provider for Vector Stores.
    """

    @staticmethod
    def get_vector_store(db: Session, backend: str = "pgvector") -> BaseVectorStore:
        """Resolve database storage backend."""
        if backend == "pgvector":
            return PGVectorStore(db)
        raise ValueError(f"Vector store backend '{backend}' not supported.")
