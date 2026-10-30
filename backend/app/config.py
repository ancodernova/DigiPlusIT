
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "ContextFlow AI"
    APP_ENV: str = "development"
    DEBUG: bool = True

    FRONTEND_URL: str = "http://localhost:3000"

    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DATABASE: str = "contextflow"

    JWT_SECRET: str = "change-this-secret-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    

    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.1-8b-instant"
    GROQ_FALLBACK_MODEL: str = ""

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
