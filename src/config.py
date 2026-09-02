from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    PINECONE_API_KEY: str = ""
    PINECONE_INDEX: str = ""
    PINECONE_EMBEDDING_MODEL: str = "multilingual-e5-large"
    MEMORY_RESOLUTION_TOP_K: int = 8
    MEMORY_SIMILARITY_THRESHOLD: float = 0.75
    LLM_CALL_DELAY_SECONDS: float = 1.0
    DATABASE_URL: str = "sqlite:///./app.db"


@lru_cache
def get_settings() -> Settings:
    return Settings()
