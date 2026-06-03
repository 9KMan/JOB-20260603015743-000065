"""Vector store service supporting pgvector, Pinecone, and Weaviate."""
from typing import Optional
from abc import ABC, abstractmethod
import numpy as np


class VectorStore(ABC):
    """Abstract vector store interface."""

    @abstractmethod
    def upsert(self, id: str, vector: list[float], metadata: dict) -> None:
        """Insert or update a vector."""
        pass

    @abstractmethod
    def search(self, vector: list[float], top_k: int = 5, filters: Optional[dict] = None) -> list[dict]:
        """Search for similar vectors."""
        pass

    @abstractmethod
    def delete(self, id: str) -> None:
        """Delete a vector."""
        pass


class PGVectorStore(VectorStore):
    """PostgreSQL with pgvector implementation."""

    def __init__(self):
        from sqlalchemy import text
        from core.database import SessionLocal
        self.SessionLocal = SessionLocal
        self._conn = None

    def _get_connection(self):
        if self._conn is None:
            self._conn = self.SessionLocal()
        return self._conn

    def setup(self):
        """Create pgvector extension and table if not exists."""
        from sqlalchemy import text
        conn = self._get_connection()
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS embeddings (
                id VARCHAR(255) PRIMARY KEY,
                vector vector(1536),
                metadata JSONB,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """))
        conn.commit()

    def upsert(self, id: str, vector: list[float], metadata: dict) -> None:
        from sqlalchemy import text
        conn = self._get_connection()
        conn.execute(
            text("""
                INSERT INTO embeddings (id, vector, metadata)
                VALUES (:id, :vector, :metadata)
                ON CONFLICT (id) DO UPDATE SET vector = :vector, metadata = :metadata
            """),
            {"id": id, "vector": vector, "metadata": metadata}
        )
        conn.commit()

    def search(self, vector: list[float], top_k: int = 5, filters: Optional[dict] = None) -> list[dict]:
        from sqlalchemy import text
        conn = self._get_connection()
        result = conn.execute(
            text("""
                SELECT id, metadata, 1 - (vector <=> :vector) as similarity
                FROM embeddings
                ORDER BY vector <=> :vector
                LIMIT :top_k
            """),
            {"vector": vector, "top_k": top_k}
        )
        return [
            {"id": row[0], "metadata": row[1], "similarity": row[2]}
            for row in result
        ]

    def delete(self, id: str) -> None:
        from sqlalchemy import text
        conn = self._get_connection()
        conn.execute(text("DELETE FROM embeddings WHERE id = :id"), {"id": id})
        conn.commit()


class PineconeStore(VectorStore):
    """Pinecone vector store implementation."""

    def __init__(self):
        import pinecone
        pinecone.init(api_key=settings.PINECONE_API_KEY)
        self.index = pinecone.Index(settings.PINECONE_INDEX_NAME)

    def upsert(self, id: str, vector: list[float], metadata: dict) -> None:
        self.index.upsert([(id, vector, metadata)])

    def search(self, vector: list[float], top_k: int = 5, filters: Optional[dict] = None) -> list[dict]:
        result = self.index.query(
            vector=vector,
            top_k=top_k,
            include_metadata=True,
            filter=filters
        )
        return [
            {"id": match.id, "metadata": match.metadata, "similarity": match.score}
            for match in result.matches
        ]

    def delete(self, id: str) -> None:
        self.index.delete(id)


class WeaviateStore(VectorStore):
    """Weaviate vector store implementation."""

    def __init__(self):
        import weaviate
        auth_config = weaviate.AuthApiKey(api_key=settings.WEAVIATE_API_KEY) if settings.WEAVIATE_API_KEY else None
        self.client = weaviate.Client(
            url=settings.WEAVIATE_URL,
            auth_client_secret=auth_config
        )

    def upsert(self, id: str, vector: list[float], metadata: dict) -> None:
        self.client.data_object.create(
            class_name="SupportBotDocument",
            uuid=id,
            vector=vector,
            properties=metadata
        )

    def search(self, vector: list[float], top_k: int = 5, filters: Optional[dict] = None) -> list[dict]:
        result = self.client.query.get(
            "SupportBotDocument",
            ["id", "content", "source", "_additional {certainty}"]
        ).with_near_vector({"vector": vector}).with_limit(top_k).do()
        return [
            {"id": obj["id"], "metadata": obj, "similarity": obj["_additional"]["certainty"]}
            for obj in result.get("data", {}).get("Get", {}).get("SupportBotDocument", [])
        ]

    def delete(self, id: str) -> None:
        self.client.data_object.delete(uuid=id, class_name="SupportBotDocument")


def get_vector_store() -> VectorStore:
    """Get the configured vector store implementation."""
    if not settings.USE_PGVECTOR:
        if settings.PINECONE_API_KEY:
            return PineconeStore()
        if settings.WEAVIATE_URL:
            return WeaviateStore()
    return PGVectorStore()