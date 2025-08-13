"""
Middleware for the Healthcare Voice AI Assistant.
Includes logging, rate limiting, and request processing middleware.
"""

import time
from typing import Callable, Dict, Any
from collections import defaultdict
import asyncio
import json

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from loguru import logger
from config.settings import get_settings


class LoggingMiddleware:
    """Middleware for logging all requests and responses."""
    
    def __init__(self, app=None):
        """Initialize the logging middleware."""
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
            
        start_time = time.time()
        
        # Log request
        logger.info(
            f"Request: {scope.get('method', 'UNKNOWN')} {scope.get('path', 'unknown')}",
            extra={
                "request_id": dict(scope.get('headers', [])).get(b"x-request-id", b"unknown").decode(),
                "client_ip": scope.get("client", ("unknown", 0))[0]
            }
        )
        
        # Process request
        try:
            await self.app(scope, receive, send)
            process_time = time.time() - start_time
            
            # Log response (we can't easily get status code in ASGI)
            logger.info(
                f"Response: {scope.get('method', 'UNKNOWN')} {scope.get('path', 'unknown')} ({process_time:.3f}s)",
                extra={
                    "process_time": process_time
                }
            )
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"Request failed: {scope.get('method', 'UNKNOWN')} {scope.get('path', 'unknown')} - {str(e)} ({process_time:.3f}s)",
                extra={
                    "error": str(e),
                    "process_time": process_time
                }
            )
            raise


class RateLimitMiddleware:
    """Middleware for rate limiting requests per client IP."""
    
    def __init__(self, app=None):
        self.app = app
        self.requests_per_minute = get_settings().max_requests_per_minute
        self.requests: Dict[str, list] = defaultdict(list)
        self.cleanup_task = None
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """Start background task to clean up old request records."""
        async def cleanup():
            while True:
                await asyncio.sleep(60)  # Clean up every minute
                current_time = time.time()
                for ip in list(self.requests.keys()):
                    # Remove requests older than 1 minute
                    self.requests[ip] = [
                        req_time for req_time in self.requests[ip] 
                        if current_time - req_time < 60
                    ]
                    # Remove IP if no recent requests
                    if not self.requests[ip]:
                        del self.requests[ip]
        
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                self.cleanup_task = asyncio.create_task(cleanup())
        except RuntimeError:
            # No event loop running, will be started later
            pass
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
            
        client_ip = scope.get("client", ("unknown", 0))[0]
        current_time = time.time()
        
        # Check rate limit
        if client_ip in self.requests:
            recent_requests = [
                req_time for req_time in self.requests[client_ip] 
                if current_time - req_time < 60
            ]
            
            if len(recent_requests) >= self.requests_per_minute:
                logger.warning(
                    f"Rate limit exceeded for IP: {client_ip}",
                    extra={
                        "client_ip": client_ip,
                        "requests_count": len(recent_requests),
                        "limit": self.requests_per_minute
                    }
                )
                
                # Send rate limit response
                await send({
                    "type": "http.response.start",
                    "status": 429,
                    "headers": [
                        (b"content-type", b"application/json"),
                        (b"retry-after", b"60")
                    ]
                })
                
                await send({
                    "type": "http.response.body",
                    "body": json.dumps({
                        "error": "Rate limit exceeded",
                        "message": f"Too many requests. Limit: {self.requests_per_minute} per minute",
                        "retry_after": 60
                    }).encode()
                })
                return
        
        # Record request
        self.requests[client_ip].append(current_time)
        
        # Process request
        await self.app(scope, receive, send)
    
    def __del__(self):
        """Cleanup when middleware is destroyed."""
        if self.cleanup_task and not self.cleanup_task.done():
            self.cleanup_task.cancel()


class RequestIDMiddleware:
    """Middleware for adding unique request IDs to all requests."""
    
    def __init__(self, app=None):
        """Initialize the request ID middleware."""
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
            
        # Generate request ID if not present
        headers = dict(scope.get('headers', []))
        if b"x-request-id" not in headers:
            import uuid
            request_id = str(uuid.uuid4())
            scope['headers'] = scope.get('headers', []) + [(b"x-request-id", request_id.encode())]
        
        await self.app(scope, receive, send)


class SecurityHeadersMiddleware:
    """Middleware for adding security headers to responses."""
    
    def __init__(self, app=None):
        """Initialize the security headers middleware."""
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
            
        # Create a custom send function to add headers
        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                # Add security headers
                headers = message.get("headers", [])
                headers.extend([
                    (b"x-content-type-options", b"nosniff"),
                    (b"x-frame-options", b"DENY"),
                    (b"x-xss-protection", b"1; mode=block"),
                    (b"referrer-policy", b"strict-origin-when-cross-origin"),
                    (b"content-security-policy", b"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'")
                ])
                message["headers"] = headers
            await send(message)
        
        await self.app(scope, receive, send_with_headers)


class HealthCheckMiddleware:
    """Middleware for health check endpoints."""
    
    def __init__(self, health_paths: list = None):
        self.health_paths = health_paths or ["/health", "/api/health"]
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        # Skip processing for health check endpoints
        if request.url.path in self.health_paths:
            return await call_next(request)
        
        # Add health check header for monitoring
        response = await call_next(request)
        response.headers["X-Health-Check"] = "false"
        
        return response
