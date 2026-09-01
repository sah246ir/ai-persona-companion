from datetime import datetime

from pydantic import BaseModel


class SessionCreate(BaseModel):
    session_token: str


class SessionResponse(BaseModel):
    id: int
    session_token: str
    created_at: datetime
    updated_at: datetime
