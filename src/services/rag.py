from typing import Any, Literal, Sequence

from pinecone import Pinecone

from src.config import get_settings


class RAGService:
    def __init__(self) -> None:
        settings = get_settings()
        self.client = Pinecone(api_key=settings.PINECONE_API_KEY)
        self.index = self.client.Index(settings.PINECONE_INDEX)
        self.embedding_model = settings.PINECONE_EMBEDDING_MODEL

    def upsert(
        self,
        id: str,
        embedding: list[float],
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.index.upsert(vectors=[(id, embedding, metadata or {})])

    def search(self, q: str, top_k: int = 5) -> list[dict[str, Any]]:
        embedding = self.embed([q])
        response = self.index.query(vector=embedding, top_k=top_k, include_metadata=True)
        return [
            {"id": match.id, "score": match.score, "metadata": match.metadata}
            for match in response.matches
        ]

    def delete(self, id: str) -> None:
        self.index.delete(ids=[id])

    def embed(
        self,
        texts: list[str],
        input_type: Literal["query", "passage"] = "passage",
    ) -> Sequence[float]:
        response = self.client.inference.embed(
            model=self.embedding_model,
            inputs=texts,
            parameters={"input_type": input_type, "truncate": "END"},
        )
        return [item.values for item in response.data]
