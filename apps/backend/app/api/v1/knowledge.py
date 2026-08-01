"""
Knowledge Base Management System — v1 REST endpoints.
"""

from __future__ import annotations

import logging
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status

from app.dependencies.auth import get_current_active_user
from app.dependencies.permissions import RequirePermission
from app.dependencies.knowledge import get_knowledge_service
from app.models.user import User
from app.schemas.knowledge import KnowledgeBaseCreate, KnowledgeBaseResponse, KnowledgeDocumentResponse
from app.services.knowledge_service import KnowledgeService

logger = logging.getLogger("knowledge_api")

router = APIRouter(
    prefix="/api/v1/knowledge",
    tags=["Knowledge Base"],
)

# Shared permission constants
_PERM_KNOWLEDGE_WRITE = "knowledge:write"
_PERM_KNOWLEDGE_READ = "knowledge:read"


@router.post(
    "",
    response_model=KnowledgeBaseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Knowledge Base",
)
def create_knowledge_base(
    payload: KnowledgeBaseCreate,
    organization_id: int = Query(..., description="ID of scoping organization"),
    current_user: User = Depends(RequirePermission(_PERM_KNOWLEDGE_WRITE)),
    service: KnowledgeService = Depends(get_knowledge_service),
) -> KnowledgeBaseResponse:
    """Create a new logical knowledge base for the tenant organization."""
    _assert_org_membership(current_user, organization_id)
    return service.create_knowledge_base(
        name=payload.name,
        description=payload.description,
        visibility=payload.visibility,
        organization_id=organization_id,
        user_id=current_user.id,
    )


@router.post(
    "/{knowledge_base_id}/documents",
    response_model=KnowledgeDocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload Document",
)
async def upload_document(
    knowledge_base_id: int,
    organization_id: int = Query(..., description="ID of scoping organization"),
    file: UploadFile = File(...),
    duplicate_policy: str = Query("reject", enum=["reject", "replace"]),
    current_user: User = Depends(RequirePermission(_PERM_KNOWLEDGE_WRITE)),
    service: KnowledgeService = Depends(get_knowledge_service),
) -> KnowledgeDocumentResponse:
    """
    Validate, process and chunk an uploaded file into a knowledge base.
    """
    _assert_org_membership(current_user, organization_id)
    kb = service.get_knowledge_base(organization_id, knowledge_base_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found.")

    file_bytes = await file.read()
    try:
        doc = service.ingest_document(
            kb_id=knowledge_base_id,
            filename=file.filename or "unknown",
            content_type=file.headers.get("content-type") or "text/plain",
            file_bytes=file_bytes,
            user_id=current_user.id,
            duplicate_policy=duplicate_policy,
        )
        return doc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get(
    "/{knowledge_base_id}/documents",
    response_model=list[KnowledgeDocumentResponse],
    summary="List Documents",
)
def list_documents(
    knowledge_base_id: int,
    organization_id: int = Query(..., description="ID of scoping organization"),
    current_user: User = Depends(RequirePermission(_PERM_KNOWLEDGE_READ)),
    service: KnowledgeService = Depends(get_knowledge_service),
) -> list[KnowledgeDocumentResponse]:
    """Retrieve all active documents in a knowledge base."""
    _assert_org_membership(current_user, organization_id)
    kb = service.get_knowledge_base(organization_id, knowledge_base_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found.")

    return service.list_documents(knowledge_base_id)


# Document base routes to avoid circular hierarchy pathing
doc_router = APIRouter(
    prefix="/api/v1/documents",
    tags=["Knowledge Base Documents"],
)


@doc_router.get(
    "/{document_id}",
    response_model=KnowledgeDocumentResponse,
    summary="Get Document",
)
def get_document(
    document_id: int,
    organization_id: int = Query(..., description="ID of scoping organization"),
    current_user: User = Depends(RequirePermission(_PERM_KNOWLEDGE_READ)),
    service: KnowledgeService = Depends(get_knowledge_service),
) -> KnowledgeDocumentResponse:
    """Get active document metadata detail."""
    _assert_org_membership(current_user, organization_id)
    doc = service.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    # ownership / tenant safety validation
    kb = service.get_knowledge_base(organization_id, doc.knowledge_base_id)
    if not kb:
        raise HTTPException(status_code=403, detail="Access denied to document.")

    return doc


@doc_router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Document",
)
def delete_document(
    document_id: int,
    organization_id: int = Query(..., description="ID of scoping organization"),
    current_user: User = Depends(RequirePermission(_PERM_KNOWLEDGE_WRITE)),
    service: KnowledgeService = Depends(get_knowledge_service),
) -> None:
    """Soft delete a document and its chunks."""
    _assert_org_membership(current_user, organization_id)
    doc = service.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    # ownership safety validation
    kb = service.get_knowledge_base(organization_id, doc.knowledge_base_id)
    if not kb:
        raise HTTPException(status_code=403, detail="Access denied to document.")

    service.delete_document(document_id)


def _assert_org_membership(user: User, organization_id: int) -> None:
    if user.is_superuser:
        return
    member_org_ids = {m.organization_id for m in user.organizations}
    if organization_id not in member_org_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of the specified organization.",
        )
