from typing import Any

from openai import OpenAI
from pydantic import BaseModel

from src.config import get_settings


class LLMService:
    def __init__(self) -> None:
        settings = get_settings()
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL

    def generate(
        self,
        system_prompt: str,
        response_model: type[BaseModel],
        tools: list[dict[str, Any]] | None = None,
    ) -> BaseModel:
        raise NotImplementedError
