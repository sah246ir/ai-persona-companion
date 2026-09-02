from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel

MemoryType = Literal[
    "preference",
    "personal_info",
    "goal",
    "relationship",
    "context",
    "other",
]

MemoryStatus = Literal["active", "inactive"]


class MemoryFact(BaseModel):
    fact: str
    message_id: int
    type: MemoryType
    importance_score: float
    confidence_score: float


class MemoryResponse(BaseModel):
    has_memory: bool
    facts: list[MemoryFact]


class MemoryRecord(BaseModel):
    memory_id: str
    session_id: int
    message_id: int
    fact: str
    type: MemoryType
    importance_score: float
    confidence_score: float
    status: MemoryStatus = "active"
    created_at: datetime
    updated_at: datetime
    superseded_by: str | None = None

    def to_metadata(self) -> dict[str, Any]:
        """Pinecone metadata must be str/number/bool/list[str] — no null, no datetime."""
        data = self.model_dump(mode="json")
        data["superseded_by"] = data["superseded_by"] or ""
        return data


class MemoryRelation(BaseModel):
    memory_id: str
    action: Literal["supersede", "update", "ignore"]
    reasoning: str


class ResolutionResponse(BaseModel):
    new_fact_status: Literal["active", "duplicate", "merged"]
    relations: list[MemoryRelation]
