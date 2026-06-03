"""Pydantic schemas for API request/response models."""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID


# Auth schemas
class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: UUID
    email: str
    username: str
    full_name: Optional[str]
    is_active: bool
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[str] = None


# Knowledge Base schemas
class KnowledgeBaseItemCreate(BaseModel):
    title: str = Field(..., max_length=500)
    content: str
    category: Optional[str] = None
    tags: list[str] = []
    metadata: dict = {}


class KnowledgeBaseItemResponse(BaseModel):
    id: UUID
    title: str
    content: str
    category: Optional[str]
    tags: list[str]
    view_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Support Ticket schemas
class SupportTicketCreate(BaseModel):
    ticket_number: str = Field(..., max_length=50)
    subject: str = Field(..., max_length=500)
    description: Optional[str] = None
    status: str = "open"
    priority: str = "medium"
    category: Optional[str] = None
    customer_email: Optional[EmailStr] = None
    customer_name: Optional[str] = None


class SupportTicketResponse(BaseModel):
    id: UUID
    ticket_number: str
    subject: str
    status: str
    priority: str
    category: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# Chat schemas
class ChatMessageRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    session_id: str = Field(..., max_length=255)
    top_k: int = Field(default=5, ge=1, le=20)
    stream: bool = False


class ChatSource(BaseModel):
    id: str
    source: str
    title: str
    similarity: float


class ChatMessageResponse(BaseModel):
    answer: str
    sources: list[ChatSource]
    model_used: str
    session_id: str


class ConversationMessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    sources: list
    created_at: datetime

    class Config:
        from_attributes = True


# Index job schemas
class IndexJobResponse(BaseModel):
    id: UUID
    job_type: str
    status: str
    total_items: int
    processed_items: int
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


# Generic response
class MessageResponse(BaseModel):
    message: str
    success: bool = True