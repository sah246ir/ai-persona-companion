from datetime import datetime

from pydantic import BaseModel


class MemoryCreate(BaseModel):
    content: str


class MemoryRead(BaseModel):
    id: int
    content: str
    created_at: datetime
