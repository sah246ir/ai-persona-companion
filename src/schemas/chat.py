from datetime import datetime
from typing import Literal

from pydantic import BaseModel

ChatSource = Literal["user", "agent"]


class ChatCreate(BaseModel):
    session_id: int
    message: str
    source: ChatSource


class ChatResponse(BaseModel):
    id: int
    session_id: int
    message: str
    source: ChatSource
    timestamp: datetime
