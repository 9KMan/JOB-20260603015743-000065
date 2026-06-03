"""Indexing API endpoints."""
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime

from core.database import get_db
from api.auth import get_current_user
from api.schemas import IndexJobResponse, MessageResponse
from models.models import IndexJob
from data_pipeline.pipeline import run_full_index
import uuid

router = APIRouter(prefix="/index", tags=["indexing"])


@router.post("/full", response_model=IndexJobResponse)
def start_full_index(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Start a full indexing job (runs in background)."""
    # Create job record
    job = IndexJob(
        id=uuid.uuid4(),
        job_type="full",
        status="pending",
        started_at=datetime.utcnow()
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Schedule background task
    def run_index():
        try:
            job.status = "running"
            db.commit()
            stats = run_full_index(db)
            job.status = "completed"
            job.total_items = stats["kb_items"] + stats["tickets"]
            job.processed_items = job.total_items
            job.completed_at = datetime.utcnow()
        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
        db.commit()

    background_tasks.add_task(run_index)

    return IndexJobResponse(
        id=job.id,
        job_type=job.job_type,
        status=job.status,
        total_items=job.total_items,
        processed_items=job.processed_items,
        error_message=job.error_message,
        started_at=job.started_at,
        completed_at=job.completed_at
    )


@router.get("/jobs", response_model=list[IndexJobResponse])
def list_index_jobs(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List recent indexing jobs."""
    jobs = db.query(IndexJob).order_by(IndexJob.created_at.desc()).limit(limit).all()
    return [
        IndexJobResponse(
            id=job.id,
            job_type=job.job_type,
            status=job.status,
            total_items=job.total_items,
            processed_items=job.processed_items,
            error_message=job.error_message,
            started_at=job.started_at,
            completed_at=job.completed_at
        )
        for job in jobs
    ]


@router.get("/jobs/{job_id}", response_model=IndexJobResponse)
def get_index_job(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get status of an indexing job."""
    job = db.query(IndexJob).filter_by(id=job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return IndexJobResponse(
        id=job.id,
        job_type=job.job_type,
        status=job.status,
        total_items=job.total_items,
        processed_items=job.processed_items,
        error_message=job.error_message,
        started_at=job.started_at,
        completed_at=job.completed_at
    )