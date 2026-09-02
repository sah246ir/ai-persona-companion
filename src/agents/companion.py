from src.prompts.companion import build_companion_prompt,CompanionPromptContextModel
from src.schemas.companion import CompanionResponse
from src.services.llm import LLMService


class CompanionAgent:
    """Generates the companion's response to the user, consistent with persona and memory context."""

    def __init__(self, llm_service: LLMService) -> None:
        self.llm_service = llm_service

    def query(self, context: CompanionPromptContextModel) -> CompanionResponse:
        system_prompt = build_companion_prompt(context)
        return self.llm_service.generate(
            system_prompt=system_prompt,
            response_model=CompanionResponse,
        )
