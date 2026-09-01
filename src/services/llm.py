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
        kwargs: dict[str, Any] = {}
        if tools is not None:
            kwargs["tools"] = tools

        completion = self.client.chat.completions.parse(
            model=self.model,
            messages=[{"role": "system", "content": system_prompt}],
            response_format=response_model,
            **kwargs,
        )
        return completion.choices[0].message.parsed
