"""
Common Pydantic schemas
Adds proper input/output validation missing from original codebase
"""
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator
from uuid import UUID


class ResponseStatus(str, Enum):
    """Response status enumeration"""
    SUCCESS = "success"
    ERROR = "error"
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"


class BaseResponse(BaseModel):
    """Base response model"""
    status: ResponseStatus
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = None


class ErrorDetail(BaseModel):
    """Error detail model"""
    code: str
    message: str
    field: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseResponse):
    """Error response model"""
    status: ResponseStatus = ResponseStatus.ERROR
    error: ErrorDetail


class SuccessResponse(BaseResponse):
    """Success response model"""
    status: ResponseStatus = ResponseStatus.SUCCESS
    data: Optional[Dict[str, Any]] = None


class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = Field(1, ge=1, description="Page number")
    size: int = Field(20, ge=1, le=100, description="Page size")
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size


class PaginatedResponse(SuccessResponse):
    """Paginated response model"""
    pagination: Dict[str, Any] = Field(default_factory=dict)
    
    @classmethod
    def create(
        cls,
        data: List[Any],
        page: int,
        size: int,
        total: int,
        **kwargs
    ):
        """Create paginated response"""
        total_pages = (total + size - 1) // size
        
        return cls(
            data={"items": data},
            pagination={
                "page": page,
                "size": size,
                "total": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            },
            **kwargs
        )


class FileInfo(BaseModel):
    """File information model"""
    name: str
    path: str
    size: int
    mime_type: Optional[str] = None
    created_at: datetime
    modified_at: Optional[datetime] = None
    
    @validator("size")
    def validate_size(cls, v):
        if v < 0:
            raise ValueError("File size cannot be negative")
        return v


class ProcessingStatus(BaseModel):
    """Processing status model"""
    id: str
    status: ResponseStatus
    progress: int = Field(0, ge=0, le=100)
    current_step: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    
    @validator("progress")
    def validate_progress(cls, v):
        if not 0 <= v <= 100:
            raise ValueError("Progress must be between 0 and 100")
        return v


class HealthCheck(BaseModel):
    """Health check response"""
    status: str = "healthy"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str
    environment: str
    services: Dict[str, str] = Field(default_factory=dict)
    
    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2024-01-01T12:00:00Z",
                "version": "2.0.0",
                "environment": "production",
                "services": {
                    "database": "healthy",
                    "redis": "healthy",
                    "weaviate": "healthy"
                }
            }
        }