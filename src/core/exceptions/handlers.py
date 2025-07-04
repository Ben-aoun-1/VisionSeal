"""
Custom exception handling
Replaces generic error handling from original codebase
"""
from typing import Any, Dict, Optional
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
import logging
import traceback
import uuid

from core.config.settings import settings


class VisionSealException(Exception):
    """Base exception for VisionSeal"""
    
    def __init__(
        self, 
        message: str, 
        error_code: str = "VISIONSEAL_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class AutomationException(VisionSealException):
    """Automation-related exceptions"""
    
    def __init__(self, message: str, source: str = "unknown", **kwargs):
        super().__init__(
            message=message,
            error_code="AUTOMATION_ERROR",
            status_code=500,
            **kwargs
        )
        self.details.update({"source": source})


class AIProcessingException(VisionSealException):
    """AI processing exceptions"""
    
    def __init__(self, message: str, operation: str = "unknown", **kwargs):
        super().__init__(
            message=message,
            error_code="AI_PROCESSING_ERROR", 
            status_code=500,
            **kwargs
        )
        self.details.update({"operation": operation})


class ValidationException(VisionSealException):
    """Input validation exceptions"""
    
    def __init__(self, message: str, field: str = "unknown", **kwargs):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=400,
            **kwargs
        )
        self.details.update({"field": field})


class SecurityException(VisionSealException):
    """Security-related exceptions"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            error_code="SECURITY_ERROR",
            status_code=403,
            **kwargs
        )


class ResourceNotFoundException(VisionSealException):
    """Resource not found exceptions"""
    
    def __init__(self, message: str, resource_type: str = "unknown", **kwargs):
        super().__init__(
            message=message,
            error_code="RESOURCE_NOT_FOUND",
            status_code=404,
            **kwargs
        )
        self.details.update({"resource_type": resource_type})


class ExceptionHandler:
    """Centralized exception handling"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def visionseal_exception_handler(
        self, 
        request: Request, 
        exc: VisionSealException
    ) -> JSONResponse:
        """Handle custom VisionSeal exceptions"""
        error_id = str(uuid.uuid4())
        
        # Log the error
        self.logger.error(
            f"VisionSeal Exception [{error_id}]: {exc.message}",
            extra={
                "error_id": error_id,
                "error_code": exc.error_code,
                "status_code": exc.status_code,
                "details": exc.details,
                "path": request.url.path,
                "method": request.method
            }
        )
        
        response_data = {
            "error": {
                "id": error_id,
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details if settings.debug else {}
            }
        }
        
        return JSONResponse(
            status_code=exc.status_code,
            content=response_data
        )
    
    async def http_exception_handler(
        self, 
        request: Request, 
        exc: HTTPException
    ) -> JSONResponse:
        """Handle FastAPI HTTP exceptions"""
        error_id = str(uuid.uuid4())
        
        self.logger.warning(
            f"HTTP Exception [{error_id}]: {exc.detail}",
            extra={
                "error_id": error_id,
                "status_code": exc.status_code,
                "path": request.url.path,
                "method": request.method
            }
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "id": error_id,
                    "code": "HTTP_ERROR",
                    "message": exc.detail
                }
            }
        )
    
    async def validation_exception_handler(
        self, 
        request: Request, 
        exc: ValidationError
    ) -> JSONResponse:
        """Handle Pydantic validation exceptions"""
        error_id = str(uuid.uuid4())
        
        self.logger.warning(
            f"Validation Exception [{error_id}]: {str(exc)}",
            extra={
                "error_id": error_id,
                "path": request.url.path,
                "method": request.method,
                "errors": exc.errors()
            }
        )
        
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "id": error_id,
                    "code": "VALIDATION_ERROR",
                    "message": "Validation failed",
                    "details": exc.errors() if settings.debug else []
                }
            }
        )
    
    async def general_exception_handler(
        self, 
        request: Request, 
        exc: Exception
    ) -> JSONResponse:
        """Handle unexpected exceptions"""
        error_id = str(uuid.uuid4())
        
        # Log full traceback for debugging
        self.logger.error(
            f"Unexpected Exception [{error_id}]: {str(exc)}",
            extra={
                "error_id": error_id,
                "path": request.url.path,
                "method": request.method,
                "traceback": traceback.format_exc() if settings.debug else None
            }
        )
        
        # Don't expose internal errors in production
        message = str(exc) if settings.debug else "Internal server error"
        
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "id": error_id,
                    "code": "INTERNAL_ERROR", 
                    "message": message
                }
            }
        )


# Global exception handler instance
exception_handler = ExceptionHandler()