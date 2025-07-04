"""
VisionSeal Complete - Refactored Main Application
Secure, well-architected replacement for the original monolithic main.py
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from core.config.settings import settings
from core.logging.setup import setup_logging, get_logger
from core.exceptions.handlers import (
    VisionSealException,
    ExceptionHandler,
    exception_handler
)
from api.middleware.security import (
    SecurityHeadersMiddleware,
    RateLimitMiddleware, 
    RequestLoggingMiddleware,
    get_cors_middleware
)
from api.routers import automation, ai
from api.schemas.common import HealthCheck

# Initialize logging
setup_logging()
logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info(
        "Starting VisionSeal Complete",
        extra={
            "version": settings.version,
            "environment": settings.environment,
            "debug": settings.debug
        }
    )
    
    # TODO: Initialize database connections
    # TODO: Initialize Redis connections
    # TODO: Initialize Weaviate connections
    # TODO: Health check external services
    
    yield
    
    # Shutdown
    logger.info("Shutting down VisionSeal Complete")
    
    # TODO: Close database connections
    # TODO: Close Redis connections
    # TODO: Close Weaviate connections


# Create FastAPI application with proper configuration
app = FastAPI(
    title=settings.project_name,
    version=settings.version,
    description="Secure, refactored VisionSeal Complete - Unified Tender Management Platform",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
    lifespan=lifespan
)

# Add security middleware (order matters!)
if settings.environment == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "*.yourdomain.com"]
    )

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# Add CORS middleware (must be last)
app.add_middleware(
    CORSMiddleware,
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

# Add exception handlers
app.add_exception_handler(VisionSealException, exception_handler.visionseal_exception_handler)
app.add_exception_handler(ValidationError, exception_handler.validation_exception_handler)
app.add_exception_handler(Exception, exception_handler.general_exception_handler)

# Include routers
app.include_router(automation.router, prefix="/api")
app.include_router(ai.router, prefix="/api")

# Mount static files securely
try:
    # Only mount if frontend directory exists
    frontend_dir = settings.base_dir / "web_interface" / "frontend"
    if frontend_dir.exists():
        app.mount(
            "/static", 
            StaticFiles(directory=str(frontend_dir)), 
            name="static"
        )
        logger.info(f"Static files mounted from: {frontend_dir}")
    else:
        logger.warning("Frontend directory not found, static files not mounted")
except Exception as e:
    logger.error(f"Failed to mount static files: {e}")


# Health check endpoint
@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Application health check"""
    # TODO: Check database connectivity
    # TODO: Check Redis connectivity
    # TODO: Check Weaviate connectivity
    # TODO: Check external service availability
    
    services_status = {
        "database": "healthy",  # TODO: Implement actual check
        "redis": "healthy",     # TODO: Implement actual check
        "weaviate": "healthy",  # TODO: Implement actual check
        "automation": "healthy", # TODO: Implement actual check
        "ai": "healthy"         # TODO: Implement actual check
    }
    
    return HealthCheck(
        status="healthy",
        version=settings.version,
        environment=settings.environment,
        services=services_status
    )


# Root endpoint
@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main application"""
    # Try to serve React app if available
    try:
        frontend_dir = settings.base_dir / "web_interface" / "frontend"
        index_path = frontend_dir / "index.html"
        
        if index_path.exists():
            with open(index_path, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
    except Exception as e:
        logger.warning(f"Failed to serve frontend: {e}")
    
    # Fallback HTML
    return HTMLResponse(
        content=f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{settings.project_name}</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ 
                    font-family: Arial, sans-serif; 
                    max-width: 800px; 
                    margin: 50px auto; 
                    padding: 20px;
                    background: #f5f5f5;
                }}
                .container {{
                    background: white;
                    padding: 40px;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .status {{ color: #28a745; font-weight: bold; }}
                .warning {{ color: #ffc107; }}
                .error {{ color: #dc3545; }}
                .info {{ background: #e7f3ff; padding: 15px; border-radius: 4px; margin: 15px 0; }}
                a {{ color: #007bff; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🎯 {settings.project_name}</h1>
                <p class="status">✅ API Server Running</p>
                <p><strong>Version:</strong> {settings.version}</p>
                <p><strong>Environment:</strong> {settings.environment}</p>
                
                <div class="info">
                    <h3>🔗 Available Endpoints:</h3>
                    <ul>
                        <li><a href="/health">Health Check</a> - System status</li>
                        <li><a href="/docs">API Documentation</a> - Interactive API docs</li>
                        <li><a href="/api/automation/capabilities">Automation Capabilities</a> - Available features</li>
                    </ul>
                </div>
                
                <div class="info">
                    <h3>🛡️ Security Features:</h3>
                    <ul>
                        <li>✅ Input validation and sanitization</li>
                        <li>✅ Secure file upload handling</li>
                        <li>✅ Rate limiting and request throttling</li>
                        <li>✅ Structured logging and monitoring</li>
                        <li>✅ Proper error handling</li>
                    </ul>
                </div>
                
                <p><em>This is the refactored, secure version of VisionSeal Complete.</em></p>
            </div>
        </body>
        </html>
        """
    )


# Simple test endpoint for development
@app.get("/api/test")
async def test_endpoint():
    """Simple test endpoint"""
    return {
        "message": "VisionSeal Complete API is working",
        "version": settings.version,
        "environment": settings.environment,
        "timestamp": "2024-01-15T12:00:00Z"
    }


if __name__ == "__main__":
    import uvicorn
    
    # Run server with proper configuration
    uvicorn.run(
        "src.main:app",
        host=settings.api.host,
        port=settings.api.port,
        workers=settings.api.workers,
        reload=settings.api.reload and settings.environment == "development",
        log_level=settings.api.log_level.lower(),
        access_log=True
    )