from datetime import datetime, timezone
from uuid import uuid4

from config import get_settings
from prompts.memory import (
    build_memory_prompt,
    build_resolution_prompt,
    MemoryPromptContextModel,
    ResolutionPromptContextModel,
)
from schemas.memory import (
    MemoryFact,
    MemoryRecord,
    MemoryRelation,
    MemoryResponse,
    ResolutionResponse,
)
from services.llm import LLMService
from services.rag import RAGService


def format_candidates(candidates: list[MemoryRecord]) -> str:
    return "\n".join(
        f'- id={c.memory_id} fact="{c.fact}" type={c.type} status={c.status} '
        f"created_at={c.created_at.isoformat()}"
        for c in candidates
    )


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

    def resolve(
        self, new_fact: MemoryFact, candidates: list[MemoryRecord]
    ) -> ResolutionResponse:
        if not candidates:
            return ResolutionResponse(new_fact_status="active", relations=[])

        system_prompt = build_resolution_prompt(
            ResolutionPromptContextModel(
                new_fact=new_fact.fact,
                candidates=format_candidates(candidates),
            )
        )
        return self.llm_service.generate(
            system_prompt=system_prompt,
            response_model=ResolutionResponse,
        )

    def _apply_relations(
        self,
        relations: list[MemoryRelation],
        new_memory_id: str,
        now: datetime,
    ) -> None:
        for rel in relations:
            if rel.action == "supersede":
                self.rag_service.update_metadata(rel.memory_id, {
                    "status": "inactive",
                    "superseded_by": new_memory_id,
                    "updated_at": now.isoformat(),
                })
            elif rel.action == "update":
                self.rag_service.update_metadata(rel.memory_id, {
                    "updated_at": now.isoformat(),
                })
            # "ignore" (or anything unexpected) is a no-op — no branch needed

    def store(self, response: MemoryResponse, session_id: int) -> list[MemoryRecord]:
        if not response.has_memory or not response.facts:
            return []

        settings = get_settings()
        now = datetime.now(timezone.utc)
        to_persist: list[MemoryRecord] = []

        for fact in response.facts:
            record = MemoryRecord(
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

            matches = self.rag_service.search(
                fact.fact,
                top_k=settings.MEMORY_RESOLUTION_TOP_K,
                session_id=session_id,
                status="active",
            )
            candidates = [
                MemoryRecord(**m["metadata"])
                for m in matches
                if m["score"] >= settings.MEMORY_SIMILARITY_THRESHOLD
            ]

            resolution = self.resolve(fact, candidates)
            self._apply_relations(resolution.relations, record.memory_id, now)

            if resolution.new_fact_status not in ("duplicate", "merged"):
                to_persist.append(record)

        if to_persist:
            embeddings = self.rag_service.embed(
                [record.fact for record in to_persist], input_type="passage"
            )
            for record, embedding in zip(to_persist, embeddings):
                self.rag_service.upsert(
                    id=record.memory_id,
                    embedding=embedding,
                    metadata=record.to_metadata(),
                )

        return to_persist
