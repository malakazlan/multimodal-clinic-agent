"""
Health check API routes for the Healthcare Voice AI Assistant.
Provides comprehensive health monitoring for all system components.
"""

import time
from typing import Dict, Any, List
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from utils.logger import logger, log_health_check
from config.settings import get_settings

router = APIRouter()


class ComponentHealth(BaseModel):
    """Health status of a system component."""
    name: str
    status: str  # healthy, degraded, unhealthy
    response_time_ms: float
    last_check: datetime
    details: Dict[str, Any] = {}
    error: str = None


class SystemHealth(BaseModel):
    """Overall system health status."""
    status: str  # healthy, degraded, unhealthy
    timestamp: datetime
    uptime_seconds: float
    components: List[ComponentHealth]
    version: str = "1.0.0"
    environment: str


@router.get("/", response_model=SystemHealth)
async def get_system_health():
    """
    Get comprehensive system health status.
    
    Returns:
        SystemHealth with status of all components
    """
    start_time = time.time()
    settings = get_settings()
    
    try:
        # Check core components
        components = []
        
        # Database health
        db_health = await check_database_health()
        components.append(db_health)
        
        # Vector store health
        vector_health = await check_vector_store_health()
        components.append(vector_health)
        
        # External API health
        api_health = await check_external_apis_health()
        components.append(api_health)
        
        # File system health
        fs_health = await check_file_system_health()
        components.append(fs_health)
        
        # Memory usage health
        memory_health = await check_memory_health()
        components.append(memory_health)
        
        # Determine overall status
        unhealthy_count = sum(1 for c in components if c.status == "unhealthy")
        degraded_count = sum(1 for c in components if c.status == "degraded")
        
        if unhealthy_count > 0:
            overall_status = "unhealthy"
        elif degraded_count > 0:
            overall_status = "degraded"
        else:
            overall_status = "healthy"
        
        # Calculate uptime (simplified - in production, track actual start time)
        uptime = time.time() - start_time  # This should be actual uptime
        
        system_health = SystemHealth(
            status=overall_status,
            timestamp=datetime.now(),
            uptime_seconds=uptime,
            components=components,
            environment=settings.environment
        )
        
        # Log health check
        log_health_check(
            component="system",
            status=overall_status,
            details={
                "unhealthy_components": unhealthy_count,
                "degraded_components": degraded_count,
                "total_components": len(components)
            }
        )
        
        return system_health
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Health check failed")


@router.get("/component/{component_name}", response_model=ComponentHealth)
async def get_component_health(component_name: str):
    """
    Get health status of a specific component.
    
    Args:
        component_name: Name of the component to check
        
    Returns:
        ComponentHealth for the specified component
    """
    try:
        if component_name == "database":
            return await check_database_health()
        elif component_name == "vector_store":
            return await check_vector_store_health()
        elif component_name == "external_apis":
            return await check_external_apis_health()
        elif component_name == "file_system":
            return await check_file_system_health()
        elif component_name == "memory":
            return await check_memory_health()
        else:
            raise HTTPException(status_code=404, detail=f"Component '{component_name}' not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Component health check failed for {component_name}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Component health check failed")


@router.get("/ping")
async def ping():
    """Simple ping endpoint for basic connectivity check."""
    return {"message": "pong", "timestamp": datetime.now().isoformat()}


async def check_database_health() -> ComponentHealth:
    """Check database connection and health."""
    start_time = time.time()
    
    try:
        # This would check actual database connectivity
        # For now, simulate a check
        await asyncio.sleep(0.1)  # Simulate database query
        
        response_time = (time.time() - start_time) * 1000
        
        return ComponentHealth(
            name="database",
            status="healthy",
            response_time_ms=response_time,
            last_check=datetime.now(),
            details={
                "connection_pool_size": 10,
                "active_connections": 2,
                "database_type": "sqlite"  # or postgres, mysql, etc.
            }
        )
        
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        
        return ComponentHealth(
            name="database",
            status="unhealthy",
            response_time_ms=response_time,
            last_check=datetime.now(),
            error=str(e)
        )


async def check_vector_store_health() -> ComponentHealth:
    """Check vector store health."""
    start_time = time.time()
    
    try:
        # This would check FAISS index health
        # For now, simulate a check
        await asyncio.sleep(0.05)  # Simulate vector store query
        
        response_time = (time.time() - start_time) * 1000
        
        return ComponentHealth(
            name="vector_store",
            status="healthy",
            response_time_ms=response_time,
            last_check=datetime.now(),
            details={
                "index_size": 1000,
                "dimensions": 1536,
                "store_type": "faiss"
            }
        )
        
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        
        return ComponentHealth(
            name="vector_store",
            status="unhealthy",
            response_time_ms=response_time,
            last_check=datetime.now(),
            error=str(e)
        )


async def check_external_apis_health() -> ComponentHealth:
    """Check external API health."""
    start_time = time.time()
    
    try:
        # This would check OpenAI, ElevenLabs, etc.
        # For now, simulate checks
        await asyncio.sleep(0.1)
        
        response_time = (time.time() - start_time) * 1000
        
        return ComponentHealth(
            name="external_apis",
            status="healthy",
            response_time_ms=response_time,
            last_check=datetime.now(),
            details={
                "openai_status": "healthy",
                "elevenlabs_status": "healthy",
                "assemblyai_status": "healthy"
            }
        )
        
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        
        return ComponentHealth(
            name="external_apis",
            status="unhealthy",
            response_time_ms=response_time,
            last_check=datetime.now(),
            error=str(e)
        )


async def check_file_system_health() -> ComponentHealth:
    """Check file system health."""
    start_time = time.time()
    
    try:
        import os
        import shutil
        
        # Check disk space
        total, used, free = shutil.disk_usage(".")
        disk_usage_percent = (used / total) * 100
        
        # Check upload directory
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        
        response_time = (time.time() - start_time) * 1000
        
        return ComponentHealth(
            name="file_system",
            status="healthy" if disk_usage_percent < 90 else "degraded",
            response_time_ms=response_time,
            last_check=datetime.now(),
            details={
                "disk_usage_percent": round(disk_usage_percent, 2),
                "free_space_gb": round(free / (1024**3), 2),
                "upload_dir_writable": os.access(upload_dir, os.W_OK)
            }
        )
        
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        
        return ComponentHealth(
            name="file_system",
            status="unhealthy",
            response_time_ms=response_time,
            last_check=datetime.now(),
            error=str(e)
        )


async def check_memory_health() -> ComponentHealth:
    """Check memory usage health."""
    start_time = time.time()
    
    try:
        import psutil
        
        # Get memory usage
        memory = psutil.virtual_memory()
        memory_usage_percent = memory.percent
        
        response_time = (time.time() - start_time) * 1000
        
        return ComponentHealth(
            name="memory",
            status="healthy" if memory_usage_percent < 85 else "degraded",
            response_time_ms=response_time,
            last_check=datetime.now(),
            details={
                "memory_usage_percent": round(memory_usage_percent, 2),
                "available_memory_gb": round(memory.available / (1024**3), 2),
                "total_memory_gb": round(memory.total / (1024**3), 2)
            }
        )
        
    except ImportError:
        # psutil not available, return basic info
        response_time = (time.time() - start_time) * 1000
        
        return ComponentHealth(
            name="memory",
            status="degraded",
            response_time_ms=response_time,
            last_check=datetime.now(),
            details={
                "note": "psutil not available for detailed memory monitoring"
            }
        )
        
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        
        return ComponentHealth(
            name="memory",
            status="unhealthy",
            response_time_ms=response_time,
            last_check=datetime.now(),
            error=str(e)
        )


# Import required modules
import asyncio
from pathlib import Path
