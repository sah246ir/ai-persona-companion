from datetime import datetime, timezone
from uuid import uuid4

from src.prompts.memory import build_memory_prompt,MemoryPromptContextModel
from src.schemas.memory import MemoryRecord, MemoryResponse
from src.services.llm import LLMService
from src.services.rag import RAGService


class MemoryAgent:
    """Analyzes recent conversation history and identifies user information worth persisting as long-term memory."""

    def __init__(self, llm_service: LLMService, rag_service: RAGService) -> None:
        self.llm_service = llm_service
        self.rag_service = rag_service

    def query(self, context: MemoryPromptContextModel) -> MemoryResponse:
        system_prompt = build_memory_prompt(context)
        return self.llm_service.generate(
            system_prompt=system_prompt,
            response_model=MemoryResponse,
        )

    def store(self, response: MemoryResponse, session_id: int) -> list[MemoryRecord]:
        if not response.has_memory or not response.facts:
            return []

        now = datetime.now(timezone.utc)
        records = [
            MemoryRecord(
                memory_id=str(uuid4()),
                session_id=session_id,
                message_id=fact.message_id,
                fact=fact.fact,
                type=fact.type,
                importance_score=fact.importance_score,
                confidence_score=fact.confidence_score,
                created_at=now,
                updated_at=now,
            )
            for fact in response.facts
        ]

        embeddings = self.rag_service.embed(
            [record.fact for record in records], input_type="passage"
        )
        for record, embedding in zip(records, embeddings):
            self.rag_service.upsert(
                id=record.memory_id,
                embedding=[embedding],
                metadata=record.to_metadata(),
            )

        return records
