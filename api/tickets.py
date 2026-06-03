"""Support tickets API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
import uuid

from core.database import get_db
from api.auth import get_current_user
from api.schemas import SupportTicketCreate, SupportTicketResponse, MessageResponse
from models.models import SupportTicket
from data_pipeline.pipeline import process_support_ticket

router = APIRouter(prefix="/tickets", tags=["support tickets"])


@router.post("/", response_model=SupportTicketResponse, status_code=status.HTTP_201_CREATED)
def create_ticket(
    ticket: SupportTicketCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new support ticket."""
    kb_ticket = SupportTicket(
        id=uuid.uuid4(),
        ticket_number=ticket.ticket_number,
        subject=ticket.subject,
        description=ticket.description,
        status=ticket.status,
        priority=ticket.priority,
        category=ticket.category,
        customer_email=ticket.customer_email,
        customer_name=ticket.customer_name,
        assigned_to=current_user.id if current_user.is_admin else None
    )
    db.add(kb_ticket)
    db.commit()
    db.refresh(kb_ticket)

    # Index the ticket
    try:
        process_support_ticket(kb_ticket, db)
    except Exception as e:
        print(f"Ticket indexing error: {e}")

    return kb_ticket


@router.get("/", response_model=list[SupportTicketResponse])
def list_tickets(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List support tickets with optional filtering."""
    query = db.query(SupportTicket)

    if status:
        query = query.filter_by(status=status)
    if priority:
        query = query.filter_by(priority=priority)
    if category:
        query = query.filter_by(category=category)

    tickets = query.order_by(SupportTicket.created_at.desc()).offset(offset).limit(limit).all()
    return tickets


@router.get("/{ticket_id}", response_model=SupportTicketResponse)
def get_ticket(
    ticket_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get a specific support ticket."""
    ticket = db.query(SupportTicket).filter_by(id=ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@router.get("/by-number/{ticket_number}", response_model=SupportTicketResponse)
def get_ticket_by_number(
    ticket_number: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get a support ticket by ticket number."""
    ticket = db.query(SupportTicket).filter_by(ticket_number=ticket_number).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@router.put("/{ticket_id}/status", response_model=MessageResponse)
def update_ticket_status(
    ticket_id: uuid.UUID,
    status: str,
    resolution: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update ticket status."""
    ticket = db.query(SupportTicket).filter_by(id=ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket.status = status
    if resolution:
        ticket.resolution = resolution
    if status == "resolved" and not ticket.resolved_at:
        from datetime import datetime
        ticket.resolved_at = datetime.utcnow()

    db.commit()
    return MessageResponse(message=f"Ticket status updated to {status}", success=True)