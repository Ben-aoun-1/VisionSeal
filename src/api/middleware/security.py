"""
Security middleware
Fixes CORS and adds security headers missing from original codebase
"""
import time
import uuid
from typing import Callable
from fastapi import Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from core.config.settings import settings
from core.security.validators import rate_limiter
from core.logging.setup import get_logger, correlation_filter

logger = get_logger("middleware")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        
        # Only add HSTS in production with HTTPS
        if settings.environment == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Enhanced rate limiting middleware with user-specific limits"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get client IP and user ID if available
        client_ip = request.client.host if request.client else "unknown"
        user_id = None
        
        # Try to extract user ID from JWT token
        try:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.replace("Bearer ", "")
                if token and len(token) > 20:  # Basic token validation
                    from core.auth.supabase_auth import auth_manager
                    from fastapi.security import HTTPAuthorizationCredentials
                    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
                    user_info = await auth_manager.get_current_user(credentials)
                    user_id = user_info.get("user_id")
        except:
            pass  # Continue with IP-based rate limiting if user extraction fails
        
        # Determine rate limit key (prefer user ID over IP)
        rate_limit_key = f"user:{user_id}" if user_id else f"ip:{client_ip}"
        
        # Exempt frequently accessed endpoints from strict rate limiting
        status_endpoints = [
            "/api/v1/scrapers/status", 
            "/api/v1/health", 
            "/health",
            "/api/v1/tenders",  # Main tenders endpoint
            "/api/v1/tenders/filters/options",  # Filter options
            "/api/v1/tenders/stats/summary"  # Dashboard stats
        ]
        is_status_endpoint = any(request.url.path.startswith(endpoint) for endpoint in status_endpoints)
        
        # Different limits for authenticated vs anonymous users
        if user_id:
            # Authenticated users get higher limits
            max_requests = 1000 if is_status_endpoint else 200
        else:
            # Anonymous users get lower limits
            max_requests = 500 if is_status_endpoint else 100
        
        # Check rate limit
        if not rate_limiter.is_allowed(rate_limit_key, max_requests=max_requests, window_seconds=3600):
            logger.warning(
                "Rate limit exceeded",
                extra={
                    "client_ip": client_ip,
                    "user_id": user_id,
                    "path": request.url.path,
                    "method": request.method,
                    "endpoint_type": "status" if is_status_endpoint else "normal",
                    "rate_limit_key": rate_limit_key
                }
            )
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later."
            )
        
        return await call_next(request)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Request logging and correlation ID middleware"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate correlation ID
        correlation_id = str(uuid.uuid4())
        correlation_filter.set_correlation_id(correlation_id)
        
        # Start timing
        start_time = time.time()
        
        # Log request
        logger.info(
            "Request started",
            extra={
                "correlation_id": correlation_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_ip": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown")
            }
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log response
            logger.info(
                "Request completed",
                extra={
                    "correlation_id": correlation_id,
                    "status_code": response.status_code,
                    "duration_ms": round(duration * 1000, 2)
                }
            )
            
            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id
            
            return response
            
        except Exception as e:
            # Calculate duration
            duration = time.time() - start_time
            
            # Log error
            logger.error(
                "Request failed",
                extra={
                    "correlation_id": correlation_id,
                    "error": str(e),
                    "duration_ms": round(duration * 1000, 2)
                }
            )
            raise


def get_cors_middleware():
    """Get properly configured CORS middleware"""
    return CORSMiddleware(
        allow_origins=settings.security.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=[
            "Authorization",
            "Content-Type", 
            "X-Requested-With",
            "Accept",
            "Origin",
            "Access-Control-Request-Method",
            "Access-Control-Request-Headers",
            "X-Correlation-ID"
        ],
        expose_headers=["X-Correlation-ID"],
        max_age=600
    )