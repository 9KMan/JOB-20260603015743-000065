"""Core configuration settings."""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # App
    APP_NAME: str = "Support AI Bot"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/support_bot"
    )

    # Vector Store (Pinecone or Weaviate)
    PINECONE_API_KEY: Optional[str] = os.getenv("PINECONE_API_KEY")
    PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME", "support-bot-index")
    WEAVIATE_URL: Optional[str] = os.getenv("WEAVIATE_URL", "http://localhost:8080")
    WEAVIATE_API_KEY: Optional[str] = os.getenv("WEAVIATE_API_KEY")

    # Use pgvector as fallback/local vector store
    USE_PGVECTOR: bool = os.getenv("USE_PGVECTOR", "true").lower() == "true"
    PGVECTOR_DIMENSION: int = 1536  # OpenAI embedding dimension

    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_EMBEDDING_MODEL: str = os.getenv(
        "OPENAI_EMBEDDING_MODEL", "text-embedding-ada-002"
    )
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")

    # Anthropic (optional)
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")

    # Auth
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8080"]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()