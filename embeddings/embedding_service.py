"""Embedding service using OpenAI."""
from typing import Optional
import openai
from core.config import settings


class EmbeddingService:
    """Service for generating text embeddings."""

    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY

    def embed_text(self, text: str, model: Optional[str] = None) -> list[float]:
        """Generate embedding for a single text."""
        model = model or settings.OPENAI_EMBEDDING_MODEL
        response = openai.embeddings.create(
            model=model,
            input=text
        )
        return response.data[0].embedding

    def embed_batch(self, texts: list[str], model: Optional[str] = None) -> list[list[float]]:
        """Generate embeddings for a batch of texts."""
        model = model or settings.OPENAI_EMBEDDING_MODEL
        response = openai.embeddings.create(
            model=model,
            input=texts
        )
        return [item.embedding for item in response.data]

    def get_embedding_dimension(self) -> int:
        """Return embedding dimension for the configured model."""
        # OpenAI ada-002 = 1536, text-embedding-3-small = 1536, text-embedding-3-large = 3072
        if settings.OPENAI_EMBEDDING_MODEL == "text-embedding-3-large":
            return 3072
        return 1536


# Singleton instance
embedding_service = EmbeddingService()