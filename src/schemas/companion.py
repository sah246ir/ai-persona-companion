from pydantic import BaseModel


class CompanionResponse(BaseModel):
    message: str
