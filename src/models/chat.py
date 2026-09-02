from datetime import datetime
from enum import Enum

from sqlmodel import Field, SQLModel


class ChatSource(str, Enum):
    user = "user"
    agent = "agent"
    validator = "validator"


class Chat(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="session.id")
    message: str
    source: ChatSource
    timestamp: datetime = Field(default_factory=datetime.utcnow)
