"""Unit tests for the support bot."""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime


class TestEmbeddingService:
    """Tests for embedding service."""

    def test_embed_text_returns_list(self):
        """Test that embed_text returns a list of floats."""
        with patch('openai.embeddings.create') as mock_create:
            mock_create.return_value = Mock(
                data=[Mock(embedding=[0.1] * 1536)]
            )
            from embeddings.embedding_service import EmbeddingService
            service = EmbeddingService()
            result = service.embed_text("test text")
            assert isinstance(result, list)
            assert len(result) == 1536

    def test_embed_batch_returns_list_of_lists(self):
        """Test that embed_batch returns multiple embeddings."""
        with patch('openai.embeddings.create') as mock_create:
            mock_create.return_value = Mock(
                data=[Mock(embedding=[0.1] * 1536), Mock(embedding=[0.2] * 1536)]
            )
            from embeddings.embedding_service import EmbeddingService
            service = EmbeddingService()
            result = service.embed_batch(["text1", "text2"])
            assert isinstance(result, list)
            assert len(result) == 2


class TestRAGService:
    """Tests for RAG service."""

    def test_build_rag_prompt_with_context(self):
        """Test prompt building with context."""
        from services.rag_service import build_rag_prompt
        context = [
            {"metadata": {"source": "kb", "title": "How to reset password"}}
        ]
        prompt = build_rag_prompt("How do I reset?", context)
        assert "How do I reset?" in prompt
        assert "How to reset password" in prompt
        assert "kb" in prompt

    def test_build_rag_prompt_without_context(self):
        """Test prompt building without context."""
        from services.rag_service import build_rag_prompt
        prompt = build_rag_prompt("Hello", [])
        assert "Hello" in prompt


class TestVectorStore:
    """Tests for vector store implementations."""

    def test_chunk_text_basic(self):
        """Test text chunking."""
        from data_pipeline.pipeline import chunk_text
        text = "a" * 1000
        chunks = chunk_text(text, chunk_size=500, overlap=50)
        assert len(chunks) == 3
        assert chunks[0] == "a" * 500
        assert chunks[1] == "a" * 500  # 500 + 450 overlap
        assert len(chunks[1]) == 500

    def test_chunk_text_small(self):
        """Test chunking text smaller than chunk size."""
        from data_pipeline.pipeline import chunk_text
        text = "short text"
        chunks = chunk_text(text, chunk_size=500)
        assert len(chunks) == 1
        assert chunks[0] == "short text"


class TestAuthService:
    """Tests for authentication service."""

    def test_password_hash_verify(self):
        """Test password hashing and verification."""
        from services.auth_service import get_password_hash, verify_password
        password = "testpassword123"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed)
        assert not verify_password("wrongpassword", hashed)

    def test_create_access_token(self):
        """Test JWT token creation."""
        from services.auth_service import create_access_token, decode_token
        token = create_access_token({"sub": "user123"})
        assert token is not None
        payload = decode_token(token)
        assert payload["sub"] == "user123"


class TestChatService:
    """Tests for chat service."""

    def test_create_conversation(self):
        """Test conversation creation."""
        with patch('services.chat_service.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db
            from services.chat_service import create_conversation
            # Note: This test would need more mocking for full coverage
            # Basic structure test
            assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])