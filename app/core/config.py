from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    DATABASE_URL: str = "sqlite+aiosqlite:///./rag_offline.db"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"
    CHROMA_PERSIST_DIRECTORY: str = "./chroma_db"
    MAX_DOCUMENT_SIZE: int = 10485760
    API_KEY_HEADER: str = "X-API-KEY"
    TENANT_ID_HEADER: str = "X-Tenant-ID"
    LOG_LEVEL: str = "INFO"


settings = Settings()
