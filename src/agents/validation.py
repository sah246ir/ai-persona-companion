from src.services.llm import LLMService


class ValidationAgent:
    """
    Future responsibilities:
    - validating memory consistency
    - validating persona consistency
    - validating generated responses
    """

    def __init__(self, llm_service: LLMService) -> None:
        self.llm_service = llm_service

    def validate_memory_consistency(self, *args, **kwargs) -> bool:
        raise NotImplementedError

    def validate_persona_consistency(self, *args, **kwargs) -> bool:
        raise NotImplementedError

    def validate_response(self, *args, **kwargs) -> bool:
        raise NotImplementedError
