from typing import Literal

from pydantic import BaseModel

MemoryType = Literal[
    "preference",
    "personal_info",
    "goal",
    "relationship",
    "context",
    "other",
]


class MemoryFact(BaseModel):
    fact: str
    message_id: int
    type: MemoryType
    importance_score: float
    confidence_score: float


class MemoryResponse(BaseModel):
    has_memory: bool
    facts: list[MemoryFact]
