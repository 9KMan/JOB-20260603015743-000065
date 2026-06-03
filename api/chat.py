"""Chat API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_db
from api.schemas import ChatMessageRequest, ChatMessageResponse, ChatSource, MessageResponse
from services.chat_service import chat
from api.auth import get_current_user

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/message", response_model=ChatMessageResponse)
def send_message(
    request: ChatMessageRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Send a chat message and get a RAG-powered response."""
    if not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query cannot be empty"
        )

    result = chat(
        query=request.query,
        session_id=request.session_id,
        user_id=str(current_user.id) if current_user else None,
        top_k=request.top_k,
        stream=request.stream
    )

    sources = [
        ChatSource(
            id=s.get("id", ""),
            source=s.get("metadata", {}).get("source", "unknown"),
            title=s.get("metadata", {}).get("title", s.get("metadata", {}).get("ticket_number", "")),
            similarity=s.get("similarity", 0.0)
        )
        for s in result.get("sources", [])
    ]

    return ChatMessageResponse(
        answer=result["answer"],
        sources=sources,
        model_used=result["model_used"],
        session_id=result["session_id"]
    )


@router.get("/history/{session_id}")
def get_history(
    session_id: str,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get conversation history for a session."""
    from services.chat_service import get_conversation_history
    messages = get_conversation_history(session_id, limit)
    return [
        {
            "id": str(m.id),
            "role": m.role,
            "content": m.content,
            "sources": m.sources or [],
            "created_at": m.created_at.isoformat()
        }
        for m in messages
    ]


@router.delete("/history/{session_id}", response_model=MessageResponse)
def clear_history(
    session_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Clear conversation history for a session."""
    from services.chat_service import get_or_create_conversation
    conv = get_or_create_conversation(session_id)
    conv.is_active = False
    db.commit()
    return MessageResponse(message="Conversation history cleared", success=True)