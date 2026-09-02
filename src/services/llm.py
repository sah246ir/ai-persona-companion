from typing import Any,TypeVar

from openai import OpenAI
from pydantic import BaseModel

from config import get_settings

T = TypeVar("T", bound=BaseModel)

class LLMService:
    def __init__(self) -> None:
        settings = get_settings()
        self.client = OpenAI(
            api_key=settings.GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
        )
        self.model = settings.GROQ_MODEL

    def generate(
        self,
        system_prompt: str,
        response_model: type[T],
        tools: list[dict[str, Any]] | None = None,
    ) -> T:
        kwargs: dict[str, Any] = {}
        if tools is not None:
            kwargs["tools"] = tools

        completion = self.client.chat.completions.parse(
            model=self.model,
            messages=[{"role": "system", "content": system_prompt}],
            response_format=response_model,
            **kwargs,
        )
        parsed =  completion.choices[0].message.parsed
        if parsed is None:
            raise ValueError("LLM returned no structured response")

        return parsed
