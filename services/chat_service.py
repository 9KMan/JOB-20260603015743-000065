"""Chat service for managing conversations."""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from models.models import Conversation, ConversationMessage, User
from services.rag_service import generate_rag_response, generate_response_stream


def create_conversation(session_id: str, user_id: Optional[str] = None) -> Conversation:
    """Create a new conversation."""
    from core.database import SessionLocal
    db = SessionLocal()
    try:
        conversation = Conversation(
            id=uuid.uuid4(),
            session_id=session_id,
            user_id=uuid.UUID(user_id) if user_id else None,
            is_active=True
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        return conversation
    finally:
        db.close()


def get_or_create_conversation(session_id: str, user_id: Optional[str] = None) -> Conversation:
    """Get existing conversation or create new one."""
    from core.database import SessionLocal
    db = SessionLocal()
    try:
        conv = db.query(Conversation).filter_by(session_id=session_id).first()
        if not conv:
            conv = create_conversation(session_id, user_id)
        return conv
    finally:
        db.close()


def add_message(
    conversation_id: uuid.UUID,
    role: str,
    content: str,
    sources: list = None,
    token_count: int = None,
    model_used: str = None
) -> ConversationMessage:
    """Add a message to a conversation."""
    from core.database import SessionLocal
    db = SessionLocal()
    try:
        message = ConversationMessage(
            id=uuid.uuid4(),
            conversation_id=conversation_id,
            role=role,
            content=content,
            sources=sources or [],
            token_count=token_count,
            model_used=model_used
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        return message
    finally:
        db.close()


def get_conversation_history(session_id: str, limit: int = 50) -> list[ConversationMessage]:
    """Get conversation history."""
    from core.database import SessionLocal
    db = SessionLocal()
    try:
        conv = db.query(Conversation).filter_by(session_id=session_id).first()
        if not conv:
            return []
        messages = db.query(ConversationMessage).filter_by(
            conversation_id=conv.id
        ).order_by(ConversationMessage.created_at.desc()).limit(limit).all()
        return list(reversed(messages))  # Return in chronological order
    finally:
        db.close()


def chat(
    query: str,
    session_id: str,
    user_id: Optional[str] = None,
    top_k: int = 5,
    stream: bool = False,
    use_anthropic: bool = False
) -> dict:
    """Process a chat message with RAG."""
    # Get or create conversation
    conversation = get_or_create_conversation(session_id, user_id)

    # Add user message
    add_message(conversation.id, "user", query)

    # Generate RAG response
    if stream:
        # For streaming, we need to handle it differently
        response_generator = generate_response_stream(
            query, top_k=top_k, use_anthropic=use_anthropic
        )
        full_response = ""
        sources = []
        model_used = "anthropic-claude" if use_anthropic else "openai"

        for chunk in response_generator:
            full_response += chunk

        # Add assistant message
        add_message(
            conversation.id, "assistant", full_response,
            sources=sources, model_used=model_used
        )

        return {
            "answer": full_response,
            "sources": sources,
            "model_used": model_used,
            "session_id": session_id
        }
    else:
        result = generate_rag_response(query, top_k=top_k, use_anthropic=use_anthropic)

        # Add assistant message
        add_message(
            conversation.id, "assistant", result["answer"],
            sources=result["sources"], model_used=result["model_used"],
            token_count=result.get("tokens_used")
        )

        return {
            "answer": result["answer"],
            "sources": result["sources"],
            "model_used": result["model_used"],
            "session_id": session_id
        }