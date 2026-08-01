"""
Memory Engine — Memory Service.

Orchestrates summarization, extraction, retrieval, and consolidation.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.memory.consolidator import Consolidator
from app.memory.exceptions import MemoryNotFoundError
from app.memory.extractor import MemoryExtractor
from app.memory.forgetting import ForgettingStrategy
from app.memory.scoring import MemoryScorer
from app.memory.summarizer import Summarizer
from app.models.memory import Memory
from app.repositories.memory_repository import MemoryRepository
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository

logger = logging.getLogger("memory_service")


class MemoryService:
    """
    Coordinates memories management and RAG orchestrator extensions.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.memory_repo = MemoryRepository(db)
        self.conv_repo = ConversationRepository(db)
        self.msg_repo = MessageRepository(db)
        self.extractor = MemoryExtractor()
        self.scorer = MemoryScorer()
        self.summarizer = Summarizer()
        self.consolidator = Consolidator()
        self.forgetting = ForgettingStrategy()

    def list_memories(
        self,
        org_id: int,
        agent_id: int | None = None,
        memory_type: str | None = None,
    ) -> list[Memory]:
        """List active memories."""
        return self.memory_repo.list_active(org_id, agent_id, memory_type)

    def get_memory(self, org_id: int, memory_id: int) -> Memory:
        """Get memory by ID."""
        mem = self.memory_repo.get_by_org_and_id(org_id, memory_id)
        if not mem:
            raise MemoryNotFoundError("Memory not found.")
        return mem

    def create_memory(
        self,
        org_id: int,
        agent_id: int,
        title: str,
        content: str,
        memory_type: str,
        importance_score: float,
        confidence_score: float,
        user_id: int,
    ) -> Memory:
        """Create a new memory manually or programmatically."""
        mem = Memory(
            organization_id=org_id,
            agent_id=agent_id,
            title=title,
            content=content,
            memory_type=memory_type,
            importance_score=importance_score,
            confidence_score=confidence_score,
            created_by=user_id,
        )
        return self.memory_repo.create(mem)

    def update_memory(
        self,
        org_id: int,
        memory_id: int,
        title: str | None,
        content: str | None,
        importance_score: float | None,
        confidence_score: float | None,
    ) -> Memory:
        """Update memory fields."""
        mem = self.get_memory(org_id, memory_id)
        if title is not None:
            mem.title = title
        if content is not None:
            mem.content = content
        if importance_score is not None:
            mem.importance_score = importance_score
        if confidence_score is not None:
            mem.confidence_score = confidence_score

        return self.memory_repo.update(mem)

    def archive_memory(self, org_id: int, memory_id: int) -> Memory:
        """Archive memory instead of soft deleting."""
        mem = self.get_memory(org_id, memory_id)
        mem.archived = True
        return self.memory_repo.update(mem)

    def delete_memory(self, org_id: int, memory_id: int) -> None:
        """Soft delete memory entry."""
        mem = self.get_memory(org_id, memory_id)
        mem.is_deleted = True
        self.memory_repo.update(mem)

    def rebuild_summary(self, conversation_id: int) -> str:
        """Fetch message logs and build new summarized text metadata."""
        messages = self.msg_repo.get_by_conversation(conversation_id)
        full_text = "\n".join([f"{m.role}: {m.content}" for m in messages])
        summary = self.summarizer.summarize(full_text)
        return summary

    async def retrieve_memories(
        self,
        org_id: int,
        agent_id: int,
        query: str,
        top_k: int = 5,
    ) -> list[Memory]:
        """
        Retrieves top relevant memories based on scoring calculations.
        """
        all_memories = self.list_memories(org_id, agent_id)
        scored = []
        for mem in all_memories:
            # Exclude expired or low-importance archived items
            if self.forgetting.is_expired(mem.expires_at) or self.forgetting.should_prune(mem.importance_score, mem.confidence_score):
                continue

            score = self.scorer.score_memory(mem.importance_score, mem.confidence_score)
            scored.append((mem, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [item[0] for item in scored[:top_k]]
