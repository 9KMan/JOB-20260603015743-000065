"""Data pipeline for processing and indexing documents."""
from typing import Optional
from dataclasses import dataclass
import uuid
from sqlalchemy.orm import Session
from models.models import KnowledgeBaseItem, SupportTicket, TicketMessage, DocumentChunk
from embeddings.embedding_service import embedding_service
from vector_store.vector_store import get_vector_store


@dataclass
class ChunkResult:
    """Result of chunking a document."""
    chunks: list[dict]  # List of {"text": str, "index": int, "metadata": dict}


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks."""
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
    return chunks


def process_knowledge_base_item(item: KnowledgeBaseItem, db: Session) -> list[DocumentChunk]:
    """Process a knowledge base item: chunk, embed, and index."""
    vector_store = get_vector_store()

    # Clean and prepare text
    text = f"{item.title}\n\n{item.content}"

    # Chunk the text
    chunk_texts = chunk_text(text)

    chunks = []
    for idx, chunk_str in enumerate(chunk_texts):
        # Generate embedding
        embedding = embedding_service.embed_text(chunk_str)

        # Store in vector DB
        chunk_id = str(uuid.uuid4())
        metadata = {
            "source": "knowledge_base",
            "item_id": str(item.id),
            "title": item.title,
            "category": item.category or "unknown"
        }
        vector_store.upsert(chunk_id, embedding, metadata)

        # Create DB record
        db_chunk = DocumentChunk(
            id=uuid.uuid4(),
            kb_item_id=item.id,
            chunk_text=chunk_str,
            chunk_index=idx,
            embedding=embedding,
            metadata=metadata
        )
        chunks.append(db_chunk)

    return chunks


def process_support_ticket(ticket: SupportTicket, db: Session) -> list[DocumentChunk]:
    """Process a support ticket and its messages: chunk, embed, and index."""
    vector_store = get_vector_store()

    # Combine ticket info
    text_parts = [
        f"Ticket #{ticket.ticket_number}",
        f"Subject: {ticket.subject}",
        f"Category: {ticket.category or 'unknown'}",
        f"Status: {ticket.status}",
    ]

    # Add resolution if available
    if ticket.resolution:
        text_parts.append(f"Resolution: {ticket.resolution}")

    # Add messages
    for msg in ticket.messages:
        if not msg.is_internal:  # Skip internal notes
            text_parts.append(f"{msg.sender_name or msg.sender_email}: {msg.content}")

    combined_text = "\n".join(text_parts)

    # Chunk and embed
    chunk_texts = chunk_text(combined_text)

    chunks = []
    for idx, chunk_str in enumerate(chunk_texts):
        embedding = embedding_service.embed_text(chunk_str)

        chunk_id = str(uuid.uuid4())
        metadata = {
            "source": "support_ticket",
            "ticket_id": str(ticket.id),
            "ticket_number": ticket.ticket_number,
            "subject": ticket.subject
        }
        vector_store.upsert(chunk_id, embedding, metadata)

        db_chunk = DocumentChunk(
            id=uuid.uuid4(),
            ticket_id=ticket.id,
            chunk_text=chunk_str,
            chunk_index=idx,
            embedding=embedding,
            metadata=metadata
        )
        chunks.append(db_chunk)

    return chunks


def run_full_index(db: Session, batch_size: int = 100) -> dict:
    """Run full indexing of all knowledge base items and support tickets."""
    vector_store = get_vector_store()
    vector_store.setup()  # Ensure table exists

    stats = {"kb_items": 0, "tickets": 0, "chunks": 0, "errors": []}

    # Process knowledge base items
    kb_items = db.query(KnowledgeBaseItem).filter_by(is_archived=False).all()
    for item in kb_items:
        try:
            chunks = process_knowledge_base_item(item, db)
            db.add_all(chunks)
            stats["kb_items"] += 1
            stats["chunks"] += len(chunks)
        except Exception as e:
            stats["errors"].append(f"KB item {item.id}: {str(e)}")

    # Process support tickets
    tickets = db.query(SupportTicket).all()
    for ticket in tickets:
        try:
            chunks = process_support_ticket(ticket, db)
            db.add_all(chunks)
            stats["tickets"] += 1
            stats["chunks"] += len(chunks)
        except Exception as e:
            stats["errors"].append(f"Ticket {ticket.ticket_number}: {str(e)}")

    db.commit()
    return stats


def retrieve_context(query: str, top_k: int = 5, source_filter: Optional[str] = None) -> list[dict]:
    """Retrieve relevant context for a query using RAG."""
    vector_store = get_vector_store()

    # Generate query embedding
    query_embedding = embedding_service.embed_text(query)

    # Search vector store
    filters = {"source": source_filter} if source_filter else None
    results = vector_store.search(query_embedding, top_k=top_k, filters=filters)

    return results