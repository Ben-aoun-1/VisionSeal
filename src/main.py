"""
VisionSeal Complete - Refactored Main Application
Secure, well-architected replacement for the original monolithic main.py
"""
from contextlib import asynccontextmanager
from datetime import datetime
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
from api.middleware.session import SessionMiddleware, session_manager
from api.routers import automation, ai, scrapers
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
app.add_middleware(SessionMiddleware, session_manager=session_manager)
app.add_middleware(RequestLoggingMiddleware)

# Add CORS middleware (must be last) - More permissive for development
if settings.environment == "development":
    # Development CORS - more permissive
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins in development
        allow_credentials=False,  # Set to False when using allow_origins=["*"]
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
        allow_headers=["*"],  # Allow all headers
    )
else:
    # Production CORS - restricted
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

# Include routers with consistent prefixes
app.include_router(automation.router, prefix="/api/v1")
app.include_router(ai.router, prefix="/api/v1")
app.include_router(scrapers.router, prefix="/api/v1")

# Import and include auth router
from api.routers import auth
app.include_router(auth.router, prefix="/api/v1")

# Import and include tenders router
from api.routers import tenders
app.include_router(tenders.router, prefix="/api/v1")

# Import and include saved tenders router
from api.routers import saved_tenders
app.include_router(saved_tenders.router, prefix="/api/v1")

# Import and include the clean automation router
from api.routers import automation_clean
app.include_router(automation_clean.router, prefix="/api/v1/automation")

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


# Health check endpoints
@app.get("/health", response_model=HealthCheck)
async def health_check():
    """
    Basic health check endpoint
    Returns overall system health with core service status
    """
    try:
        from core.health.checks import health_manager
        
        # Perform health checks for core services only (faster)
        services_detailed = await health_manager.check_all_services(include_external=False)
        
        # Convert detailed status to simple string format for compatibility
        services_status = {}
        for service_name, details in services_detailed.items():
            services_status[service_name] = details.get('status', 'unknown')
        
        # Determine overall status
        overall_status = health_manager.determine_overall_status(services_detailed)
        
        return HealthCheck(
            status=overall_status,
            version=settings.version,
            environment=settings.environment,
            services=services_status
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        # Fallback to basic response if health check system fails
        return HealthCheck(
            status="degraded",
            version=settings.version,
            environment=settings.environment,
            services={
                "database": "unknown",
                "redis": "unknown", 
                "weaviate": "unknown",
                "automation": "unknown",
                "ai": "unknown"
            }
        )


@app.get("/health/detailed")
async def detailed_health_check(include_external: bool = False):
    """
    Detailed health check endpoint
    Returns comprehensive health information with response times and details
    """
    try:
        from core.health.checks import health_manager
        
        # Perform comprehensive health checks
        services_detailed = await health_manager.check_all_services(include_external=include_external)
        
        # Determine overall status
        overall_status = health_manager.determine_overall_status(services_detailed)
        
        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "version": settings.version,
            "environment": settings.environment,
            "services": services_detailed,
            "summary": {
                "total_services": len(services_detailed),
                "healthy_services": len([s for s in services_detailed.values() if s.get('status') == 'healthy']),
                "degraded_services": len([s for s in services_detailed.values() if s.get('status') == 'degraded']),
                "unhealthy_services": len([s for s in services_detailed.values() if s.get('status') == 'unhealthy']),
                "unknown_services": len([s for s in services_detailed.values() if s.get('status') == 'unknown'])
            }
        }
        
    except Exception as e:
        logger.error(f"Detailed health check failed: {str(e)}")
        return {
            "status": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "version": settings.version,
            "environment": settings.environment,
            "error": str(e),
            "services": {}
        }


@app.get("/health/live")
async def liveness_check():
    """
    Kubernetes/Docker liveness probe endpoint
    Fast check to determine if application is running
    """
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}


@app.get("/health/ready")
async def readiness_check():
    """
    Kubernetes/Docker readiness probe endpoint  
    Checks if application is ready to serve traffic
    """
    try:
        from core.health.checks import health_manager
        
        # Check critical services only (database + automation)
        db_check = await health_manager.db_checker.check_supabase()
        automation_check = await health_manager.automation_checker.check_automation_system()
        
        # Application is ready if critical services are healthy or degraded
        critical_statuses = [db_check.status.value, automation_check.status.value]
        
        if all(status in ['healthy', 'degraded'] for status in critical_statuses):
            return {
                "status": "ready",
                "timestamp": datetime.utcnow().isoformat(),
                "critical_services": {
                    "database": db_check.status.value,
                    "automation": automation_check.status.value
                }
            }
        else:
            return {
                "status": "not_ready", 
                "timestamp": datetime.utcnow().isoformat(),
                "critical_services": {
                    "database": db_check.status.value,
                    "automation": automation_check.status.value
                }
            }
            
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        return {
            "status": "not_ready",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }


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

# Add explicit OPTIONS handler for problematic endpoints
@app.options("/api/v1/{path:path}")
async def options_handler(path: str):
    """Handle OPTIONS requests for all API endpoints"""
    return {"message": "OK"}

# Add redirect for tenders endpoint without trailing slash
@app.get("/api/v1/tenders")
async def redirect_tenders_no_slash(request: Request):
    """Redirect /api/v1/tenders to /api/v1/tenders/ with query params"""
    from fastapi.responses import RedirectResponse
    query_string = str(request.url.query)
    redirect_url = "/api/v1/tenders/"
    if query_string:
        redirect_url += f"?{query_string}"
    return RedirectResponse(url=redirect_url, status_code=307)

# Add redirects for saved-tenders endpoints without trailing slash
@app.get("/api/v1/saved-tenders")
async def redirect_saved_tenders_get_no_slash(request: Request):
    """Redirect /api/v1/saved-tenders to /api/v1/saved-tenders/ with query params"""
    from fastapi.responses import RedirectResponse
    query_string = str(request.url.query)
    redirect_url = "/api/v1/saved-tenders/"
    if query_string:
        redirect_url += f"?{query_string}"
    return RedirectResponse(url=redirect_url, status_code=307)

@app.post("/api/v1/saved-tenders")
async def redirect_saved_tenders_post_no_slash(request: Request):
    """Redirect POST /api/v1/saved-tenders to /api/v1/saved-tenders/"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/api/v1/saved-tenders/", status_code=307)


if __name__ == "__main__":
    import uvicorn
    
    # Run server with proper configuration
    # Pass app object directly to avoid module path issues
    
    # Handle workers and reload configuration properly
    # If workers=0 in env, use single process mode without workers parameter
    # If reload=true, use single process mode without workers parameter
    
    use_workers = settings.api.workers > 0 and settings.environment == "production" and not settings.api.reload
    
    if use_workers:
        # Production mode with multiple workers
        uvicorn.run(
            app,
            host=settings.api.host,
            port=settings.api.port,
            workers=settings.api.workers,
            log_level=settings.api.log_level.lower(),
            access_log=True
        )
    else:
        # Single process mode (development or single worker production)
        uvicorn.run(
            app,
            host=settings.api.host,
            port=settings.api.port,
            reload=settings.api.reload and settings.environment == "development",
            log_level=settings.api.log_level.lower(),
            access_log=True
        )