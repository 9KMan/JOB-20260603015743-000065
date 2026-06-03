"""Database models for the support bot."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from core.database import Base


class User(Base):
    """User model."""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    conversations = relationship("Conversation", back_populates="user")
    knowledge_base_items = relationship("KnowledgeBaseItem", back_populates="created_by_user")


class KnowledgeBaseItem(Base):
    """Knowledge base article/document."""
    __tablename__ = "knowledge_base_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False, index=True)
    content = Column(Text, nullable=False)
    category = Column(String(100), index=True)
    tags = Column(JSON, default=list)
    metadata = Column(JSON, default=dict)
    embedding = Column(JSON, nullable=True)  # Store embedding vector
    is_archived = Column(Boolean, default=False)
    view_count = Column(Integer, default=0)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    created_by_user = relationship("User", back_populates="knowledge_base_items")
    chunks = relationship("DocumentChunk", back_populates="kb_item")


class SupportTicket(Base):
    """Historical support ticket."""
    __tablename__ = "support_tickets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_number = Column(String(50), unique=True, index=True, nullable=False)
    subject = Column(String(500), nullable=False)
    description = Column(Text)
    status = Column(String(50), index=True)  # open, closed, pending
    priority = Column(String(20), index=True)  # low, medium, high, urgent
    category = Column(String(100), index=True)
    customer_email = Column(String(255), index=True)
    customer_name = Column(String(255))
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    resolution = Column(Text)
    embedding = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    # Relationships
    assignee = relationship("User", foreign_keys=[assigned_to])
    messages = relationship("TicketMessage", back_populates="ticket")


class TicketMessage(Base):
    """Message within a support ticket."""
    __tablename__ = "ticket_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id = Column(UUID(as_uuid=True), ForeignKey("support_tickets.id"), nullable=False)
    sender_email = Column(String(255), nullable=False)
    sender_name = Column(String(255))
    sender_type = Column(String(20))  # customer, agent, bot
    content = Column(Text, nullable=False)
    is_internal = Column(Boolean, default=False)  # Internal notes
    embedding = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    ticket = relationship("SupportTicket", back_populates="messages")


class DocumentChunk(Base):
    """Chunked document for embedding/indexing."""
    __tablename__ = "document_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    kb_item_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_base_items.id"), nullable=True)
    ticket_id = Column(UUID(as_uuid=True), ForeignKey("support_tickets.id"), nullable=True)
    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    embedding = Column(JSON, nullable=True)
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    kb_item = relationship("KnowledgeBaseItem", back_populates="chunks")
    ticket = relationship("SupportTicket")


class Conversation(Base):
    """Chat conversation session."""
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    session_id = Column(String(255), unique=True, index=True, nullable=False)
    context = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("ConversationMessage", back_populates="conversation", order_by="ConversationMessage.created_at")


class ConversationMessage(Base):
    """Message in a chat conversation."""
    __tablename__ = "conversation_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    sources = Column(JSON, default=list)  # Retrieved context for RAG
    token_count = Column(Integer)
    model_used = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")


class IndexJob(Base):
    """Background indexing job status."""
    __tablename__ = "index_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_type = Column(String(50), nullable=False)  # full, incremental, single
    status = Column(String(20), default="pending")  # pending, running, completed, failed
    total_items = Column(Integer, default=0)
    processed_items = Column(Integer, default=0)
    error_message = Column(Text)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)