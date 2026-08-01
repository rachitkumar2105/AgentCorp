"""
RAG Engine — RAG Service.

Coordinates document retrieval, ranking and prompt injections.
"""

from __future__ import annotations

import logging
from sqlalchemy.orm import Session

from app.models.knowledge_document import KnowledgeDocument
from app.models.knowledge_chunk import KnowledgeChunk
from app.rag.chunk_selector import ChunkSelector
from app.rag.context_formatter import ContextFormatter
from app.rag.embedding_service import EmbeddingService
from app.rag.query_rewriter import QueryRewriter
from app.rag.ranker import Ranker
from app.rag.reranker import ReRanker
from app.rag.retriever import Retriever
from app.repositories.document_repository import DocumentRepository
from app.repositories.chunk_repository import ChunkRepository

logger = logging.getLogger("rag_service")


class RAGService:
    """
    Coordinates RAG operations: rewrites, retrieval, ranking, context formatting.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.doc_repo = DocumentRepository(db)
        self.chunk_repo = ChunkRepository(db)
        self.embedding_service = EmbeddingService(db)
        self.query_rewriter = QueryRewriter()
        self.retriever = Retriever(db)
        self.ranker = Ranker()
        self.reranker = ReRanker()
        self.chunk_selector = ChunkSelector()
        self.context_formatter = ContextFormatter()

    async def rebuild_embeddings(
        self,
        kb_id: int,
        provider_name: str = "openai",
    ) -> dict[str, int]:
        """
        Recompute embeddings for all documents belonging to a knowledge base.
        """
        docs = self.doc_repo.list_by_kb(kb_id)
        processed_count = 0
        for doc in docs:
            await self.embedding_service.generate_and_store_document_embeddings(
                doc=doc,
                provider_name=provider_name,
            )
            processed_count += 1
        return {"documents_processed": processed_count}

    async def retrieve_context(
        self,
        kb_id: int,
        query: str,
        top_k: int = 5,
        max_tokens: int = 2000,
    ) -> str:
        """
        Runs the RAG pipeline to generate prompt context for a query.
        """
        cleaned_query = self.query_rewriter.rewrite_query(query)
        candidates = await self.retriever.retrieve_candidates(kb_id, cleaned_query, top_k)
        ranked = self.ranker.rank_candidates(candidates)
        reranked = self.reranker.rerank(ranked)
        selected_ids = self.chunk_selector.select_chunks(reranked, top_k, max_tokens)

        chunks_data = []
        for cid in selected_ids:
            chunk = self.chunk_repo.get(cid)
            if chunk:
                doc = self.doc_repo.get(chunk.document_id)
                chunks_data.append({
                    "text": chunk.text,
                    "document_name": doc.filename if doc else "Unknown",
                })

        return self.context_formatter.format_context(chunks_data)
