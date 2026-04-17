"""Application configuration via pydantic-settings."""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Google Gemini
    GEMINI_API_KEY: str = Field(default="", description="Google Gemini API key")

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://documind:documind_secret@localhost:5432/documind",
        description="Async PostgreSQL connection URL",
    )

    # Redis
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL",
    )

    # JWT Authentication
    SECRET_KEY: str = Field(
        default="change-this-secret-key-in-production",
        description="Secret key for JWT encoding",
    )
    ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=60, description="Access token expiration in minutes"
    )

    # File uploads
    UPLOAD_DIR: str = Field(default="./uploads", description="Upload directory path")
    MAX_FILE_SIZE_MB: int = Field(
        default=100, description="Maximum file size in megabytes"
    )

    # Application
    APP_NAME: str = Field(default="DocuMind AI", description="Application name")
    DEBUG: bool = Field(default=False, description="Debug mode")

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = Field(
        default=60, description="API requests per minute per user"
    )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


settings = Settings()
