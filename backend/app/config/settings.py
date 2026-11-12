from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "InterviewIQ API"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"
    cors_origins: list[str] = ["http://localhost:5173"]
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/interviewiq"
    upload_dir: str = "uploads"
    max_upload_size_bytes: int = 10 * 1024 * 1024
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.8-flash"
    gemini_timeout_seconds: float = 60.0
    ai_rate_limit_per_minute: int = 30
    database_pool_size: int = 5
    database_max_overflow: int = 10
    rag_chroma_dir: str = "chroma_data"
    rag_embedding_model: str = "all-MiniLM-L6-v2"
    rag_chunk_size: int = 800
    rag_chunk_overlap: int = 120
    rag_top_k: int = 5

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
