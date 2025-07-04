"""
Security Middleware for VisionSeal
Implements security headers, rate limiting, and request validation
"""
import time
import json
from typing import Dict, Any, Optional
from collections import defaultdict, deque
from datetime import datetime, timedelta
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from .security_config import get_security_config

class SecurityMiddleware(BaseHTTPMiddleware):
    """Comprehensive security middleware"""
    
    def __init__(self, app, config=None):
        super().__init__(app)
        self.config = config or get_security_config()
        self.rate_limiter = InMemoryRateLimiter(self.config)
        
    async def dispatch(self, request: Request, call_next):
        """Process request through security checks"""
        
        # Apply rate limiting
        if not self.rate_limiter.is_allowed(self._get_client_ip(request)):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded"}
            )
        
        # Validate request size
        if hasattr(request, "content_length") and request.content_length:
            if request.content_length > self.config.MAX_JSON_SIZE:
                return JSONResponse(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    content={"detail": "Request too large"}
                )
        
        # Process request
        response = await call_next(request)
        
        # Apply security headers
        self._apply_security_headers(response)
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        # Check for forwarded headers first
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
            
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
            
        return request.client.host if request.client else "unknown"
    
    def _apply_security_headers(self, response: Response):
        """Apply security headers to response"""
        for header_name, header_value in self.config.SECURITY_HEADERS.items():
            response.headers[header_name] = header_value

class InMemoryRateLimiter:
    """In-memory rate limiter implementation"""
    
    def __init__(self, config):
        self.config = config
        self.requests: Dict[str, deque] = defaultdict(deque)
        self.blocked: Dict[str, datetime] = {}
        
    def is_allowed(self, client_ip: str) -> bool:
        """Check if request is allowed for client"""
        current_time = datetime.now()
        
        # Check if client is currently blocked
        if client_ip in self.blocked:
            if current_time < self.blocked[client_ip]:
                return False
            else:
                del self.blocked[client_ip]
        
        # Clean old requests
        window_start = current_time - timedelta(minutes=self.config.RATE_LIMIT_WINDOW_MINUTES)
        client_requests = self.requests[client_ip]
        
        # Remove old requests
        while client_requests and client_requests[0] < window_start:
            client_requests.popleft()
        
        # Check rate limit
        if len(client_requests) >= self.config.RATE_LIMIT_REQUESTS:
            # Block client for window duration
            self.blocked[client_ip] = current_time + timedelta(
                minutes=self.config.RATE_LIMIT_WINDOW_MINUTES
            )
            return False
        
        # Add current request
        client_requests.append(current_time)
        return True

class InputValidationMiddleware(BaseHTTPMiddleware):
    """Input validation and sanitization middleware"""
    
    def __init__(self, app, config=None):
        super().__init__(app)
        self.config = config or get_security_config()
        
    async def dispatch(self, request: Request, call_next):
        """Validate and sanitize input data"""
        
        # Only process JSON requests
        if request.headers.get("content-type") == "application/json":
            try:
                body = await request.body()
                if body:
                    data = json.loads(body)
                    sanitized_data = self._sanitize_data(data)
                    
                    # Replace request body with sanitized data
                    request._body = json.dumps(sanitized_data).encode()
                    
            except (json.JSONDecodeError, UnicodeDecodeError):
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"detail": "Invalid JSON data"}
                )
        
        return await call_next(request)
    
    def _sanitize_data(self, data: Any) -> Any:
        """Recursively sanitize data"""
        if isinstance(data, dict):
            return {
                key: self._sanitize_data(value) 
                for key, value in data.items()
            }
        elif isinstance(data, list):
            return [self._sanitize_data(item) for item in data]
        elif isinstance(data, str):
            return self.config.sanitize_string(data)
        else:
            return data

def create_security_middleware_stack(app):
    """Create complete security middleware stack"""
    
    # Add security middleware in reverse order (last added executes first)
    app.add_middleware(InputValidationMiddleware)
    app.add_middleware(SecurityMiddleware)
    
    return app