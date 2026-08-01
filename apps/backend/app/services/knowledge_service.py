"""
Knowledge Base Management System — Service Layer.
"""

from __future__ import annotations

import logging
from typing import Any
from sqlalchemy.orm import Session

from app.knowledge.chunker import Chunker
from app.knowledge.document_processor import DocumentProcessor
from app.knowledge.exceptions import DuplicateDocumentError, KnowledgeBaseError
from app.knowledge.metadata import MetadataExtractor
from app.knowledge.validators import DocumentValidator
from app.models.knowledge_base import KnowledgeBase
from app.models.knowledge_document import KnowledgeDocument
from app.models.knowledge_chunk import KnowledgeChunk
from app.models.user import User
from app.repositories.knowledge_repository import KnowledgeBaseRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.chunk_repository import ChunkRepository

logger = logging.getLogger("knowledge_service")


class KnowledgeService:
    """
    Orchestrates the ingestion, document states, chunking processes and database writes.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.kb_repo = KnowledgeBaseRepository(db)
        self.doc_repo = DocumentRepository(db)
        self.chunk_repo = ChunkRepository(db)
        self.doc_processor = DocumentProcessor()
        self.chunker = Chunker()
        self.meta_extractor = MetadataExtractor()

    def create_knowledge_base(
        self,
        name: str,
        description: str | None,
        visibility: str,
        organization_id: int,
        user_id: int,
    ) -> KnowledgeBase:
        """Create a new logical knowledge base."""
        kb = KnowledgeBase(
            organization_id=organization_id,
            name=name,
            description=description,
            visibility=visibility,
            created_by=user_id,
        )
        return self.kb_repo.create(kb)

    def list_knowledge_bases(self, organization_id: int) -> list[KnowledgeBase]:
        """List active knowledge bases for an organization."""
        return self.kb_repo.list_by_org(organization_id)

    def get_knowledge_base(self, organization_id: int, kb_id: int) -> KnowledgeBase | None:
        """Retrieve a specific knowledge base."""
        return self.kb_repo.get_by_org_and_id(organization_id, kb_id)

    def list_documents(self, kb_id: int) -> list[KnowledgeDocument]:
        """List all active documents within a knowledge base."""
        return self.doc_repo.list_by_kb(kb_id)

    def get_document(self, doc_id: int) -> KnowledgeDocument | None:
        """Get document details if not deleted."""
        return self.doc_repo.get_active(doc_id)

    def delete_document(self, doc_id: int) -> None:
        """Soft delete a document and all its corresponding chunks."""
        doc = self.doc_repo.get_active(doc_id)
        if not doc:
            return

        doc.is_deleted = True
        self.doc_repo.update(doc)

        chunks = self.chunk_repo.list_by_document(doc_id)
        for chunk in chunks:
            chunk.is_deleted = True
            self.chunk_repo.update(chunk)

    def ingest_document(
        self,
        kb_id: int,
        filename: str,
        content_type: str,
        file_bytes: bytes,
        user_id: int,
        duplicate_policy: str = "reject",
    ) -> KnowledgeDocument:
        """
        Runs the full document processing pipeline:
          1. Validation checks
          2. Duplicate checksum checks
          3. Parsing text & extraction
          4. Segment chunking
          5. Database persistence
        """
        file_size = len(file_bytes)
        # Validate format & size
        DocumentValidator.validate_file(filename, content_type, file_size)

        # Calculate checksum
        checksum = DocumentValidator.calculate_checksum(file_bytes)

        # Duplicate check
        existing = self.doc_repo.get_by_checksum_in_kb(checksum, kb_id)
        if existing:
            if duplicate_policy == "reject":
                raise DuplicateDocumentError("A document with the same content already exists in this knowledge base.")
            elif duplicate_policy == "replace":
                self.delete_document(existing.id)

        # Create Document entry with status VALIDATING
        doc = KnowledgeDocument(
            knowledge_base_id=kb_id,
            filename=filename,
            original_filename=filename,
            mime_type=content_type,
            file_size=file_size,
            checksum=checksum,
            processing_status="VALIDATING",
            uploaded_by=user_id,
        )
        doc = self.doc_repo.create(doc)

        try:
            # Process & Extract
            doc.processing_status = "PROCESSING"
            self.doc_repo.update(doc)
            text, raw_meta = self.doc_processor.process(file_bytes, content_type)

            # Metadata merge
            doc.processing_status = "CHUNKING"
            self.doc_repo.update(doc)
            merged_meta = self.meta_extractor.extract_metadata(filename, text, raw_meta)
            doc.metadata_json = merged_meta

            # Generate chunks
            chunks_data = self.chunker.chunk_text(text)

            for idx, chunk_info in enumerate(chunks_data):
                chunk = KnowledgeChunk(
                    document_id=doc.id,
                    chunk_index=idx,
                    text=chunk_info["text"],
                    token_count=chunk_info["token_count"],
                    character_count=chunk_info["character_count"],
                    metadata_json={"source_document": filename},
                )
                self.chunk_repo.create(chunk)

            doc.processing_status = "READY"
            self.doc_repo.update(doc)
            return doc

        except Exception as exc:
            logger.error("Ingestion failed for document %s: %s", filename, exc, exc_info=True)
            doc.processing_status = "FAILED"
            self.doc_repo.update(doc)
            raise KnowledgeBaseError(f"Document ingestion failed: {exc}")
