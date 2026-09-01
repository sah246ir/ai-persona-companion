from datetime import datetime

from sqlmodel import Field, SQLModel


class Session(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    session_token: str = Field(unique=True, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
