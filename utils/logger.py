"""
Logging utilities for the Healthcare Voice AI Assistant.
Provides structured logging with different output formats and levels.
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from loguru import logger
from config.settings import get_settings


def setup_logging() -> None:
    """Setup logging configuration for the application."""
    settings = get_settings()
    
    # Remove default handler
    logger.remove()
    
    # Console handler with color
    if settings.log_format == "json":
        logger.add(
            sys.stdout,
            format=lambda record: json.dumps({
                "timestamp": record["time"].isoformat(),
                "level": record["level"].name,
                "message": record["message"],
                "module": record["module"],
                "function": record["function"],
                "line": record["line"],
                "extra": record["extra"]
            }),
            level=settings.log_level,
            colorize=True
        )
    else:
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                   "<level>{level: <8}</level> | "
                   "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                   "<level>{message}</level>",
            level=settings.log_level,
            colorize=True
        )
    
    # File handler for errors
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logger.add(
        log_dir / "error.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        level="ERROR",
        rotation="10 MB",
        retention="30 days",
        compression="zip"
    )
    
    # File handler for all logs
    logger.add(
        log_dir / "app.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        level="DEBUG",
        rotation="50 MB",
        retention="7 days",
        compression="zip"
    )
    
    # Performance metrics logging
    if settings.enable_metrics:
        logger.add(
            log_dir / "metrics.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {message}",
            level="INFO",
            filter=lambda record: "metrics" in record["extra"],
            rotation="100 MB",
            retention="1 day"
        )


def log_health_check(component: str, status: str, details: Dict[str, Any] = None) -> None:
    """Log health check information for monitoring."""
    log_data = {
        "component": component,
        "status": status,
        "timestamp": datetime.now().isoformat()
    }
    
    if details:
        log_data.update(details)
    
    logger.info(f"Health check: {component} - {status}", extra={"health_check": True, "data": log_data})


def log_performance_metric(operation: str, duration_ms: float, metadata: Dict[str, Any] = None) -> None:
    """Log performance metrics for monitoring and optimization."""
    log_data = {
        "operation": operation,
        "duration_ms": duration_ms,
        "timestamp": datetime.now().isoformat()
    }
    
    if metadata:
        log_data.update(metadata)
    
    logger.info(f"Performance: {operation} took {duration_ms:.2f}ms", extra={"metrics": True, "data": log_data})


def log_user_interaction(user_id: str, action: str, details: Dict[str, Any] = None) -> None:
    """Log user interactions for analytics and debugging."""
    log_data = {
        "user_id": user_id,
        "action": action,
        "timestamp": datetime.now().isoformat()
    }
    
    if details:
        log_data.update(details)
    
    logger.info(f"User interaction: {user_id} - {action}", extra={"user_interaction": True, "data": log_data})


def log_rag_query(query: str, results_count: int, response_time_ms: float, top_results: list = None) -> None:
    """Log RAG query information for performance monitoring."""
    log_data = {
        "query": query,
        "results_count": results_count,
        "response_time_ms": response_time_ms,
        "timestamp": datetime.now().isoformat()
    }
    
    if top_results:
        log_data["top_results"] = top_results[:3]  # Log only top 3 results
    
    logger.info(f"RAG query: {query[:100]}... returned {results_count} results in {response_time_ms:.2f}ms", 
                extra={"rag_query": True, "data": log_data})


def log_voice_processing(audio_format: str, duration_seconds: float, processing_type: str, 
                        success: bool, error: str = None) -> None:
    """Log voice processing operations."""
    log_data = {
        "audio_format": audio_format,
        "duration_seconds": duration_seconds,
        "processing_type": processing_type,
        "success": success,
        "timestamp": datetime.now().isoformat()
    }
    
    if error:
        log_data["error"] = error
    
    if success:
        logger.info(f"Voice processing: {processing_type} completed for {audio_format} audio ({duration_seconds:.2f}s)", 
                    extra={"voice_processing": True, "data": log_data})
    else:
        logger.error(f"Voice processing: {processing_type} failed for {audio_format} audio - {error}", 
                     extra={"voice_processing": True, "data": log_data})


def log_safety_check(content: str, action: str, risk_level: str, details: Dict[str, Any] = None) -> None:
    """Log safety and compliance checks."""
    log_data = {
        "content_preview": content[:100] + "..." if len(content) > 100 else content,
        "action": action,
        "risk_level": risk_level,
        "timestamp": datetime.now().isoformat()
    }
    
    if details:
        log_data.update(details)
    
    logger.warning(f"Safety check: {action} - {risk_level} risk detected", 
                   extra={"safety_check": True, "data": log_data})


# Export logger instance for use in other modules
__all__ = ["logger", "setup_logging", "log_health_check", "log_performance_metric", 
           "log_user_interaction", "log_rag_query", "log_voice_processing", "log_safety_check"]
