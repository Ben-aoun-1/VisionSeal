#!/usr/bin/env python3
"""
VisionSeal API Package
FastAPI-based REST API for tender data management
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    app = FastAPI(
        title="VisionSeal API",
        description="RESTful API for African tender opportunities",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # Configure CORS for React frontend
    origins = [
        "http://localhost:3000",  # React dev server
        "http://localhost:3001",  # Alternative React port
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ]
    
    # Add production origins if available
    if os.getenv("ALLOWED_ORIGINS"):
        origins.extend(os.getenv("ALLOWED_ORIGINS").split(","))
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    
    # Add compression middleware
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Include routers
    from .routers import tenders, automation, auth
    
    app.include_router(tenders.router)
    app.include_router(automation.router)
    app.include_router(auth.router)
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return JSONResponse(
            content={
                "status": "healthy",
                "service": "VisionSeal API",
                "version": "1.0.0"
            }
        )
    
    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint"""
        return JSONResponse(
            content={
                "message": "VisionSeal API",
                "version": "1.0.0",
                "docs": "/docs",
                "endpoints": {
                    "tenders": "/api/v1/tenders",
                    "automation": "/api/v1/automation",
                    "auth": "/api/v1/auth"
                }
            }
        )
    
    return app

# Create app instance
app = create_app()