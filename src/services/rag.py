from typing import Any

from pinecone import Pinecone

from src.config import get_settings


class RAGService:
    def __init__(self) -> None:
        settings = get_settings()
        self.client = Pinecone(api_key=settings.PINECONE_API_KEY)
        self.index = self.client.Index(settings.PINECONE_INDEX)

    def upsert(
        self,
        id: str,
        embedding: list[float],
        metadata: dict[str, Any] | None = None,
    ) -> None:
        raise NotImplementedError

    def search(self, embedding: list[float], top_k: int = 5) -> list[dict[str, Any]]:
        raise NotImplementedError

    def delete(self, id: str) -> None:
        raise NotImplementedError
