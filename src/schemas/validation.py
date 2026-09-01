from pydantic import BaseModel


class ValidationResponse(BaseModel):
    is_valid: bool
    memory_score: float
    persona_score: float
    unsupported_claims_score: float
    persona_drift_score: float
    description: str
