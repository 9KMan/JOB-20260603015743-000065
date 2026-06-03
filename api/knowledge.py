"""Knowledge base API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
import uuid

from core.database import get_db
from api.auth import get_current_user
from api.schemas import KnowledgeBaseItemCreate, KnowledgeBaseItemResponse, MessageResponse
from models.models import KnowledgeBaseItem
from data_pipeline.pipeline import process_knowledge_base_item

router = APIRouter(prefix="/knowledge-base", tags=["knowledge base"])


@router.post("/items", response_model=KnowledgeBaseItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(
    item: KnowledgeBaseItemCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new knowledge base item."""
    kb_item = KnowledgeBaseItem(
        id=uuid.uuid4(),
        title=item.title,
        content=item.content,
        category=item.category,
        tags=item.tags,
        metadata=item.metadata,
        created_by=current_user.id
    )
    db.add(kb_item)
    db.commit()
    db.refresh(kb_item)

    # Trigger embedding/indexing in background
    try:
        process_knowledge_base_item(kb_item, db)
    except Exception as e:
        # Log error but don't fail the request
        print(f"Indexing error: {e}")

    return kb_item


@router.get("/items", response_model=list[KnowledgeBaseItemResponse])
def list_items(
    category: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List knowledge base items with optional filtering."""
    query = db.query(KnowledgeBaseItem).filter_by(is_archived=False)

    if category:
        query = query.filter_by(category=category)

    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (KnowledgeBaseItem.title.ilike(search_filter)) |
            (KnowledgeBaseItem.content.ilike(search_filter))
        )

    items = query.order_by(KnowledgeBaseItem.created_at.desc()).offset(offset).limit(limit).all()
    return items


@router.get("/items/{item_id}", response_model=KnowledgeBaseItemResponse)
def get_item(
    item_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get a specific knowledge base item."""
    item = db.query(KnowledgeBaseItem).filter_by(id=item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    # Increment view count
    item.view_count += 1
    db.commit()

    return item


@router.put("/items/{item_id}", response_model=KnowledgeBaseItemResponse)
def update_item(
    item_id: uuid.UUID,
    item_update: KnowledgeBaseItemCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update a knowledge base item."""
    item = db.query(KnowledgeBaseItem).filter_by(id=item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    item.title = item_update.title
    item.content = item_update.content
    item.category = item_update.category
    item.tags = item_update.tags
    item.metadata = item_update.metadata

    db.commit()
    db.refresh(item)

    # Re-index
    try:
        process_knowledge_base_item(item, db)
    except Exception as e:
        print(f"Re-indexing error: {e}")

    return item


@router.delete("/items/{item_id}", response_model=MessageResponse)
def delete_item(
    item_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Archive a knowledge base item (soft delete)."""
    item = db.query(KnowledgeBaseItem).filter_by(id=item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    item.is_archived = True
    db.commit()

    return MessageResponse(message="Item archived successfully", success=True)