from prompts.validation import build_validation_prompt,ValidationPromptContextModel
from schemas.validation import ValidationResponse
from services.llm import LLMService


class ValidationAgent:
    """Evaluates whether a generated response is consistent with the provided context."""

    def __init__(self, llm_service: LLMService) -> None:
        self.llm_service = llm_service

    def query(self, context: ValidationPromptContextModel) -> ValidationResponse:
        system_prompt = build_validation_prompt(context)
        return self.llm_service.generate(
            system_prompt=system_prompt,
            response_model=ValidationResponse,
        )
