"""
Automation-related schemas
Defines proper data models for automation operations
"""
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date
from enum import Enum
from pydantic import BaseModel, Field, field_validator, HttpUrl

from api.schemas.common import BaseResponse, ResponseStatus, ProcessingStatus


class AutomationSource(str, Enum):
    """Automation source enumeration"""
    UNGM = "ungm"
    TUNIPAGES = "tunipages"
    BOTH = "both"


class TenderStatus(str, Enum):
    """Tender status enumeration"""
    ACTIVE = "active"
    CLOSED = "closed"
    CANCELLED = "cancelled"
    PENDING = "pending"


class TenderCategory(str, Enum):
    """Tender category enumeration"""
    CONSULTING = "consulting"
    SUPPLY = "supply"
    SERVICES = "services"
    WORKS = "works"
    OTHER = "other"


class AutomationStartRequest(BaseModel):
    """Request to start automation"""
    source: AutomationSource
    max_pages: Optional[int] = Field(10, ge=1, le=50)
    headless: bool = True
    target_countries: Optional[List[str]] = None
    search_terms: Optional[List[str]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "source": "ungm",
                "max_pages": 10,
                "headless": True,
                "target_countries": ["Tunisia", "Morocco"],
                "search_terms": ["consulting", "technical assistance"]
            }
        }


class DeepDiveRequest(BaseModel):
    """Request for deep dive extraction"""
    item_id: str = Field(..., min_length=1)
    source: AutomationSource
    extract_documents: bool = True
    extract_requirements: bool = True
    
    @field_validator("item_id")
    @classmethod
    def validate_item_id(cls, v):
        if not v.strip():
            raise ValueError("Item ID cannot be empty")
        return v.strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "item_id": "tender_12345",
                "source": "ungm",
                "extract_documents": True,
                "extract_requirements": True
            }
        }


class TenderInfo(BaseModel):
    """Tender information model"""
    id: str
    title: str
    source: str
    country: Optional[str] = None
    organization: Optional[str] = None
    published: Optional[date] = None
    deadline: Optional[date] = None
    status: TenderStatus = TenderStatus.ACTIVE
    category: Optional[TenderCategory] = None
    url: Optional[HttpUrl] = None
    description: Optional[str] = None
    budget: Optional[str] = None
    currency: Optional[str] = None
    
    # Enhanced fields
    details_extracted: bool = False
    documents_found: int = 0
    enhanced: bool = False
    is_starred: bool = False
    can_deep_dive: bool = True
    relevance_score: Optional[float] = Field(None, ge=0, le=1)
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "ungm_12345",
                "title": "Technical Assistance for Digital Transformation",
                "source": "UNGM Enhanced",
                "country": "Tunisia",
                "organization": "UNDP",
                "published": "2024-01-15",
                "deadline": "2024-02-15",
                "status": "active",
                "category": "consulting",
                "url": "https://www.ungm.org/tender/12345",
                "relevance_score": 0.85
            }
        }


class TenderDetails(TenderInfo):
    """Detailed tender information"""
    requirements: Optional[str] = None
    specifications: Optional[str] = None
    contact_info: Optional[Dict[str, str]] = None
    documents: List[Dict[str, str]] = Field(default_factory=list)
    milestones: List[Dict[str, Any]] = Field(default_factory=list)
    evaluation_criteria: Optional[str] = None
    submission_method: Optional[str] = None
    
    extracted_at: Optional[datetime] = None
    extraction_session_id: Optional[str] = None


class AutomationStatusResponse(BaseResponse):
    """Automation status response"""
    session_id: Optional[str] = None
    progress: int = Field(0, ge=0, le=100)
    current_step: Optional[str] = None
    items_found: int = 0
    items_processed: int = 0
    enhanced: bool = False
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "processing",
                "session_id": "session_12345",
                "progress": 75,
                "current_step": "Extracting tender details",
                "items_found": 25,
                "items_processed": 18,
                "enhanced": True
            }
        }


class ExtractionResults(BaseResponse):
    """Extraction results response"""
    data: List[TenderInfo] = Field(default_factory=list)
    total_items: int = 0
    session_id: Optional[str] = None
    extraction_time: Optional[datetime] = None
    source: Optional[AutomationSource] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "data": [],
                "total_items": 25,
                "session_id": "session_12345",
                "extraction_time": "2024-01-15T12:00:00Z",
                "source": "ungm"
            }
        }