"""
Main application entry point for the Healthcare Voice AI Assistant.
FastAPI application with comprehensive middleware and API routing.
"""

import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
import time

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings import get_settings, is_production, is_development
from app.api import api_router
from app.middleware import RateLimitMiddleware, LoggingMiddleware
from utils.logger import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Healthcare Voice AI Assistant...")
    setup_logging()
    
    # Create necessary directories
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("data/vector_store", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Healthcare Voice AI Assistant...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title="Healthcare Voice AI Assistant",
        description="A production-grade RAG system with voice capabilities for healthcare applications",
        version="1.0.0",
        docs_url="/docs" if is_development() else None,
        redoc_url="/redoc" if is_development() else None,
        lifespan=lifespan
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Security middleware
    if is_production():
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*"]  # Configure appropriately for production
        )
    
    # Custom middleware
    app.add_middleware(LoggingMiddleware)
    
    if settings.enable_rate_limiting:
        app.add_middleware(RateLimitMiddleware)
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Global exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "message": "An unexpected error occurred. Please try again later."
            }
        )
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint for monitoring."""
        return {
            "status": "healthy",
            "service": "Healthcare Voice AI Assistant",
            "version": "1.0.0",
            "environment": settings.environment
        }
    
    # Test endpoint for debugging
    @app.get("/test")
    async def test_endpoint():
        """Test endpoint for debugging."""
        return {
            "message": "API is working!",
            "timestamp": time.time(),
            "endpoints": {
                "health": "/health",
                "chat": "/api/chat/send",
                "voice": "/api/voice/transcribe",
                "docs": "/docs"
            }
        }
    
    # Include API routes
    app.include_router(api_router, prefix="/api")
    
    # Mount static files for frontend
    frontend_path = Path(__file__).parent / "frontend" / "static"
    if frontend_path.exists():
        app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")
    
    return app


app = create_app()


if __name__ == "__main__":
    settings = get_settings()
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload and is_development(),
        workers=settings.workers,
        log_level=settings.log_level.lower(),
        access_log=True
    )
