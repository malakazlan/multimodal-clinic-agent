"""
API router for the Healthcare Voice AI Assistant.
Combines all route modules into a single router.
"""

from fastapi import APIRouter

from .voice import router as voice_router
from .chat import router as chat_router
from .health import router as health_router
from .docs import router as docs_router

# Create main API router
api_router = APIRouter()

# Include all route modules
api_router.include_router(voice_router, prefix="/voice", tags=["voice"])
api_router.include_router(chat_router, prefix="/chat", tags=["chat"])
api_router.include_router(health_router, prefix="/health", tags=["health"])
api_router.include_router(docs_router, prefix="/docs", tags=["documents"])

# Add global prefix if needed
# api_router.prefix = "/api"
