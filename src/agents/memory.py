from src.prompts.memory import build_memory_prompt
from src.schemas.memory import MemoryResponse
from src.services.llm import LLMService


class MemoryAgent:
    """Analyzes recent conversation history and identifies user information worth persisting as long-term memory."""

    def __init__(self, llm_service: LLMService) -> None:
        self.llm_service = llm_service

    def query(self, context: dict) -> MemoryResponse:
        system_prompt = build_memory_prompt(context)
        return self.llm_service.generate(
            system_prompt=system_prompt,
            response_model=MemoryResponse,
        )
