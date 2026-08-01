"""
RAG Engine — v1 REST endpoints.
"""

from __future__ import annotations

import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies.auth import get_current_active_user
from app.dependencies.permissions import RequirePermission
from app.dependencies.knowledge import get_knowledge_service
from app.dependencies.rag import get_rag_service
from app.models.user import User
from app.schemas.rag import SearchRequest, SearchResponse, SearchResultItem
from app.services.knowledge_service import KnowledgeService
from app.services.rag_service import RAGService

logger = logging.getLogger("rag_api")

router = APIRouter(
    prefix="/api/v1/knowledge",
    tags=["RAG Engine"],
)

# Permissions
_PERM_KNOWLEDGE_WRITE = "knowledge:write"
_PERM_KNOWLEDGE_READ = "knowledge:read"


@router.post(
    "/{knowledge_base_id}/embeddings/rebuild",
    status_code=status.HTTP_200_OK,
    summary="Rebuild Embeddings",
)
async def rebuild_embeddings(
    knowledge_base_id: int,
    organization_id: int = Query(..., description="ID of scoping organization"),
    provider: str = Query("openai", description="Embedding provider"),
    current_user: User = Depends(RequirePermission(_PERM_KNOWLEDGE_WRITE)),
    kb_service: KnowledgeService = Depends(get_knowledge_service),
    rag_service: RAGService = Depends(get_rag_service),
) -> dict:
    """
    Rebuild and recalculate vector representations for all chunks in a knowledge base.
    """
    _assert_org_membership(current_user, organization_id)
    kb = kb_service.get_knowledge_base(organization_id, knowledge_base_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found.")

    res = await rag_service.rebuild_embeddings(knowledge_base_id, provider)
    return res


@router.get(
    "/documents/{document_id}/embeddings",
    status_code=status.HTTP_200_OK,
    summary="Embedding Status",
)
def get_embedding_status(
    document_id: int,
    organization_id: int = Query(..., description="ID of scoping organization"),
    current_user: User = Depends(RequirePermission(_PERM_KNOWLEDGE_READ)),
    kb_service: KnowledgeService = Depends(get_knowledge_service),
) -> dict:
    """
    Check the current embedding status for a document.
    """
    _assert_org_membership(current_user, organization_id)
    doc = kb_service.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    # ownership isolation
    kb = kb_service.get_knowledge_base(organization_id, doc.knowledge_base_id)
    if not kb:
        raise HTTPException(status_code=403, detail="Access denied.")

    chunks = kb_service.chunk_repo.list_by_document(document_id)
    embedded_count = sum(1 for c in chunks if c.embedding_status == "READY")

    return {
        "document_id": document_id,
        "total_chunks": len(chunks),
        "embedded_chunks": embedded_count,
        "status": "READY" if len(chunks) > 0 and embedded_count == len(chunks) else "PENDING",
    }


@router.post(
    "/search",
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Search Knowledge",
)
async def search_knowledge(
    payload: SearchRequest,
    organization_id: int = Query(..., description="ID of scoping organization"),
    current_user: User = Depends(RequirePermission(_PERM_KNOWLEDGE_READ)),
    kb_service: KnowledgeService = Depends(get_knowledge_service),
    rag_service: RAGService = Depends(get_rag_service),
) -> SearchResponse:
    """
    Exposes raw matched chunk search vectors for RAG pipeline validation.
    """
    _assert_org_membership(current_user, organization_id)
    kb = kb_service.get_knowledge_base(organization_id, payload.knowledge_base_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found.")

    candidates = await rag_service.retriever.retrieve_candidates(
        payload.knowledge_base_id,
        payload.query,
        payload.top_k,
    )

    results = []
    for cid, score, meta in candidates:
        chunk = rag_service.chunk_repo.get(cid)
        if chunk:
            results.append(SearchResultItem(
                chunk_id=cid,
                score=score,
                text=chunk.text,
                metadata=meta,
            ))

    return SearchResponse(query=payload.query, results=results)


def _assert_org_membership(user: User, organization_id: int) -> None:
    if user.is_superuser:
        return
    member_org_ids = {m.organization_id for m in user.organizations}
    if organization_id not in member_org_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of the specified organization.",
        )
