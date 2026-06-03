"""Main FastAPI application."""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from core.config import settings
from core.database import engine, Base
from api import auth, chat, knowledge, tickets, indexing

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown."""
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")
    yield
    # Shutdown
    logger.info("Shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered support bot with RAG-style retrieval",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "message": str(exc)}
    )


# Include routers with /api/v1 prefix
app.include_router(auth.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(knowledge.router, prefix="/api/v1")
app.include_router(tickets.router, prefix="/api/v1")
app.include_router(indexing.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": settings.APP_VERSION}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=settings.DEBUG)