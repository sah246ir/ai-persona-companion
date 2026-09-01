from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    PINECONE_API_KEY: str = ""
    PINECONE_INDEX: str = ""
    DATABASE_URL: str = "sqlite:///./app.db"


@lru_cache
def get_settings() -> Settings:
    return Settings()
