
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "ContextFlow AI"
    APP_ENV: str = "development"
    DEBUG: bool = False

    FRONTEND_URL: str = "http://localhost:3000"

    MONGODB_URL: str
    MONGODB_DATABASE: str = "contextflow"

    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    

    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.1-8b-instant"
    GROQ_FALLBACK_MODEL: str = ""
    GROQ_TRANSCRIPTION_MODEL: str = "whisper-large-v3-turbo"
    MAX_UPLOAD_SIZE_BYTES: int = 25 * 1024 * 1024
    LOCAL_STORAGE_PATH: str = "storage"
    PINECONE_API_KEY: str = ""
    PINECONE_INDEX_NAME: str = ""
    PINECONE_NAMESPACE_PREFIX: str = "contextflow"
    PINECONE_CLOUD: str = ""
    PINECONE_REGION: str = ""
    EMBEDDING_PROVIDER: str = "pinecone_inference"
    EMBEDDING_MODEL: str = "llama-text-embed-v2"
    EMBEDDING_DIMENSIONS: int = 1024

    LOG_LEVEL: str = "INFO"
    REQUEST_TIMEOUT_SECONDS: float = 30.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
