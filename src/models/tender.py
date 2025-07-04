"""
Tender data models
Based on original VisionSeal data structures
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Boolean, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class TenderSource(str, Enum):
    """Tender source platforms"""
    UNGM = "ungm"
    TUNIPAGES = "tunipages"
    COMBINED = "combined"


class TenderStatus(str, Enum):
    """Tender status enumeration"""
    ACTIVE = "active"
    EXPIRED = "expired"
    CLOSED = "closed"
    DRAFT = "draft"


class TenderCategory(str, Enum):
    """Tender categories"""
    CONSULTING = "consulting"
    TECHNICAL_ASSISTANCE = "technical_assistance"
    ADVISORY_SERVICES = "advisory_services"
    CAPACITY_BUILDING = "capacity_building"
    BUSINESS_DEVELOPMENT = "business_development"
    ENTREPRENEURSHIP = "entrepreneurship"
    OTHER = "other"


class Tender(Base):
    """Main tender model"""
    __tablename__ = "tenders"
    
    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    source = Column(String, nullable=False)  # TenderSource enum
    country = Column(String)
    organization = Column(String)
    promoter = Column(String)  # For TuniPages tenders
    
    # Dates
    published_date = Column(DateTime)
    deadline = Column(DateTime)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Status and categorization
    status = Column(String, default=TenderStatus.ACTIVE.value)
    category = Column(String)
    tender_type = Column(String)  # For TuniPages type field
    
    # URLs and references
    url = Column(String)
    original_url = Column(String)
    
    # Scoring and analysis
    relevance_score = Column(Float, default=0.0)
    details_extracted = Column(Boolean, default=False)
    documents_found = Column(Integer, default=0)
    enhanced = Column(Boolean, default=False)
    
    # Additional metadata
    raw_data = Column(JSON)  # Store original scraped data
    extraction_metadata = Column(JSON)  # Store processing metadata
    
    # Relationships
    documents = relationship("TenderDocument", back_populates="tender")


class TenderDocument(Base):
    """Tender document model"""
    __tablename__ = "tender_documents"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tender_id = Column(String, ForeignKey("tenders.id"), nullable=False)
    
    # Document info
    filename = Column(String, nullable=False)
    original_filename = Column(String)
    file_path = Column(String)
    file_size = Column(Integer)
    mime_type = Column(String)
    
    # Processing status
    processed = Column(Boolean, default=False)
    processing_status = Column(String, default="pending")
    processing_error = Column(Text)
    
    # AI analysis results
    content_extracted = Column(Text)
    sections_extracted = Column(JSON)
    vector_stored = Column(Boolean, default=False)
    
    # Metadata
    upload_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    processed_date = Column(DateTime)
    
    # Relationships
    tender = relationship("Tender", back_populates="documents")


class AutomationSession(Base):
    """Automation session tracking"""
    __tablename__ = "automation_sessions"
    
    id = Column(String, primary_key=True)  # UUID
    source = Column(String, nullable=False)  # TenderSource enum
    
    # Session info
    status = Column(String, default="running")  # running, completed, failed, cancelled
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime)
    
    # Progress tracking
    total_pages = Column(Integer, default=0)
    current_page = Column(Integer, default=0)
    tenders_found = Column(Integer, default=0)
    tenders_processed = Column(Integer, default=0)
    
    # Configuration
    search_params = Column(JSON)  # Store search parameters
    max_pages = Column(Integer)
    
    # Results
    output_file = Column(String)  # Path to JSON output
    error_message = Column(Text)
    performance_metrics = Column(JSON)
    
    # User context
    user_id = Column(String)
    
    # Note: AutomationSession doesn't belong to a specific tender
    # It creates multiple tenders, so no direct relationship


class AIProcessingJob(Base):
    """AI processing job tracking"""
    __tablename__ = "ai_processing_jobs"
    
    id = Column(String, primary_key=True)  # UUID
    job_type = Column(String, nullable=False)  # document_analysis, response_generation, chat
    
    # Job status
    status = Column(String, default="pending")  # pending, running, completed, failed
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Input data
    input_data = Column(JSON)  # Store job parameters
    document_id = Column(Integer)  # Reference to TenderDocument
    
    # Output data
    result_data = Column(JSON)  # Store processing results
    output_files = Column(JSON)  # List of generated files
    
    # Processing metadata
    model_used = Column(String)
    processing_time = Column(Float)
    token_usage = Column(JSON)  # Store token consumption data
    
    # Error handling
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    
    # User context
    user_id = Column(String)


# Pydantic models for API
class TenderBase(BaseModel):
    """Base tender schema"""
    title: str
    description: Optional[str] = None
    source: TenderSource
    country: Optional[str] = None
    organization: Optional[str] = None
    promoter: Optional[str] = None
    published_date: Optional[datetime] = None
    deadline: Optional[datetime] = None
    status: TenderStatus = TenderStatus.ACTIVE
    category: Optional[TenderCategory] = None
    tender_type: Optional[str] = None
    url: Optional[str] = None
    relevance_score: float = 0.0


class TenderCreate(TenderBase):
    """Schema for creating tenders"""
    id: str
    raw_data: Optional[Dict[str, Any]] = None


class TenderUpdate(BaseModel):
    """Schema for updating tenders"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TenderStatus] = None
    category: Optional[TenderCategory] = None
    relevance_score: Optional[float] = None
    details_extracted: Optional[bool] = None
    documents_found: Optional[int] = None


class TenderResponse(TenderBase):
    """Schema for tender responses"""
    id: str
    created_at: datetime
    updated_at: datetime
    details_extracted: bool
    documents_found: int
    enhanced: bool
    
    class Config:
        from_attributes = True


class AutomationSessionCreate(BaseModel):
    """Schema for creating automation sessions"""
    source: TenderSource
    search_params: Optional[Dict[str, Any]] = None
    max_pages: Optional[int] = 50


class AutomationSessionResponse(BaseModel):
    """Schema for automation session responses"""
    id: str
    source: TenderSource
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    total_pages: int
    current_page: int
    tenders_found: int
    tenders_processed: int
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True


class AIProcessingJobCreate(BaseModel):
    """Schema for creating AI processing jobs"""
    job_type: str
    input_data: Dict[str, Any]
    document_id: Optional[int] = None


class AIProcessingJobResponse(BaseModel):
    """Schema for AI processing job responses"""
    id: str
    job_type: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    result_data: Optional[Dict[str, Any]] = None
    processing_time: Optional[float] = None
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True