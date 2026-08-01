"""
RAG Engine — Vector Store pgvector Implementation.
"""

from __future__ import annotations

import logging
from typing import Any, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.rag.filters import MetadataFilters
from app.rag.vector_store import BaseVectorStore

logger = logging.getLogger("pgvector_store")


class PGVectorStore(BaseVectorStore):
    """
    pgvector implementation for vector database storage.
    Note: Embeddings metadata is stored inside pgvector schema extensions.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    async def create_index(self, kb_id: int, dimensions: int) -> None:
        # Create extension if not present
        self.db.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        # Create the raw coordinates storage table if not exists
        self.db.execute(text(
            f"CREATE TABLE IF NOT EXISTS kb_embeddings_{kb_id} ("
            "  chunk_id INTEGER PRIMARY KEY,"
            f"  embedding vector({dimensions}),"
            "  metadata JSONB"
            ");"
        ))
        self.db.commit()

    async def upsert(
        self,
        kb_id: int,
        chunk_id: int,
        vector: list[float],
        metadata: dict[str, Any],
    ) -> None:
        import json
        sql = text(
            f"INSERT INTO kb_embeddings_{kb_id} (chunk_id, embedding, metadata) "
            "VALUES (:chunk_id, :embedding, :metadata) "
            "ON CONFLICT (chunk_id) DO UPDATE SET "
            "embedding = EXCLUDED.embedding, metadata = EXCLUDED.metadata;"
        )
        self.db.execute(
            sql,
            {
                "chunk_id": chunk_id,
                "embedding": str(vector),
                "metadata": json.dumps(metadata),
            },
        )
        self.db.commit()

    async def batch_upsert(
        self,
        kb_id: int,
        items: list[tuple[int, list[float], dict[str, Any]]],
    ) -> None:
        import json
        sql = text(
            f"INSERT INTO kb_embeddings_{kb_id} (chunk_id, embedding, metadata) "
            "VALUES (:chunk_id, :embedding, :metadata) "
            "ON CONFLICT (chunk_id) DO UPDATE SET "
            "embedding = EXCLUDED.embedding, metadata = EXCLUDED.metadata;"
        )
        for chunk_id, vector, metadata in items:
            self.db.execute(
                sql,
                {
                    "chunk_id": chunk_id,
                    "embedding": str(vector),
                    "metadata": json.dumps(metadata),
                },
            )
        self.db.commit()

    async def delete(self, kb_id: int, chunk_id: int) -> None:
        self.db.execute(
            text(f"DELETE FROM kb_embeddings_{kb_id} WHERE chunk_id = :chunk_id;"),
            {"chunk_id": chunk_id},
        )
        self.db.commit()

    async def search(
        self,
        kb_id: int,
        query_vector: list[float],
        top_k: int,
        filters: Optional[MetadataFilters] = None,
    ) -> list[tuple[int, float, dict[str, Any]]]:
        # cosine distance operator '<=>' in pgvector
        sql_str = (
            f"SELECT chunk_id, (1 - (embedding <=> :query)) as similarity, metadata "
            f"FROM kb_embeddings_{kb_id} "
        )
        where_clauses = []
        params: dict[str, Any] = {"query": str(query_vector), "top_k": top_k}

        if filters:
            if filters.document_id is not None:
                where_clauses.append("(metadata->>'document_id')::int = :doc_id")
                params["doc_id"] = filters.document_id
            if filters.language:
                where_clauses.append("metadata->>'language' = :lang")
                params["lang"] = filters.language

        if where_clauses:
            sql_str += " WHERE " + " AND ".join(where_clauses)

        sql_str += " ORDER BY embedding <=> :query LIMIT :top_k;"
        res = self.db.execute(text(sql_str), params).fetchall()

        return [(row[0], float(row[1]), row[2] if isinstance(row[2], dict) else {}) for row in res]

    async def health_check(self) -> bool:
        try:
            self.db.execute(text("SELECT 1;"))
            return True
        except Exception:
            return False
