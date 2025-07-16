"""
AI-related schemas
Defines proper data models for AI operations
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, field_validator

from api.schemas.common import BaseResponse, FileInfo


class AIOperation(str, Enum):
    """AI operation types"""
    DOCUMENT_ANALYSIS = "document_analysis"
    RESPONSE_GENERATION = "response_generation"
    QUESTION_ANSWERING = "question_answering"
    SECTOR_ANALYSIS = "sector_analysis"


class DocumentType(str, Enum):
    """Supported document types"""
    PDF = "pdf"
    DOCX = "docx"
    PPTX = "pptx"


class ReportType(str, Enum):
    """AI report types matching frontend configuration"""
    PROPOSAL = "proposal"
    ANALYSIS = "analysis"
    SUMMARY = "summary"


class ReportTone(str, Enum):
    """Report tone options"""
    PROFESSIONAL = "professional"
    TECHNICAL = "technical"
    PERSUASIVE = "persuasive"


class ReportLength(str, Enum):
    """Report length options"""
    BRIEF = "brief"          # 1-2 pages
    DETAILED = "detailed"    # 3-5 pages
    COMPREHENSIVE = "comprehensive"  # 6+ pages


class ChatRequest(BaseModel):
    """Chat/Q&A request"""
    question: str = Field(..., min_length=1, max_length=1000)
    document_path: Optional[str] = None
    context: Optional[str] = None
    
    @field_validator("question")
    @classmethod
    def validate_question(cls, v):
        if not v.strip():
            raise ValueError("Question cannot be empty")
        return v.strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "What are the main requirements for this tender?",
                "document_path": "/uploads/tender_document.pdf",
                "context": "additional context if needed"
            }
        }


class DocumentAnalysisRequest(BaseModel):
    """Document analysis request"""
    operation: AIOperation = AIOperation.DOCUMENT_ANALYSIS
    extract_summary: bool = True
    analyze_sector: bool = True
    analyze_country: bool = True
    generate_response: bool = False
    
    class Config:
        json_schema_extra = {
            "example": {
                "operation": "document_analysis",
                "extract_summary": True,
                "analyze_sector": True,
                "analyze_country": True,
                "generate_response": False
            }
        }


class SectorAnalysis(BaseModel):
    """Sector analysis result"""
    sector: Optional[str] = None
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    keywords: List[str] = Field(default_factory=list)
    
    class Config:
        json_schema_extra = {
            "example": {
                "sector": "Information Technology",
                "confidence": 0.85,
                "keywords": ["software", "digital", "technology"]
            }
        }


class CountryAnalysis(BaseModel):
    """Country analysis result"""
    country: Optional[str] = None
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    region: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "country": "Tunisia",
                "confidence": 0.92,
                "region": "MENA"
            }
        }


class DocumentAnalysisResult(BaseModel):
    """Document analysis result"""
    summary: Optional[str] = None
    sector_analysis: Optional[SectorAnalysis] = None
    country_analysis: Optional[CountryAnalysis] = None
    key_points: List[str] = Field(default_factory=list)
    requirements: Optional[str] = None
    deadlines: List[str] = Field(default_factory=list)
    
    # Metadata
    document_type: Optional[DocumentType] = None
    processing_time: Optional[float] = None
    model_used: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "summary": "This is a tender for IT consulting services...",
                "sector_analysis": {
                    "sector": "Information Technology",
                    "confidence": 0.85
                },
                "country_analysis": {
                    "country": "Tunisia", 
                    "confidence": 0.92
                },
                "key_points": ["Technical expertise required", "5-year experience minimum"],
                "processing_time": 2.5,
                "model_used": "gpt-4-turbo"
            }
        }


class ResponseGenerationResult(BaseModel):
    """AI response generation result"""
    response_file: Optional[FileInfo] = None
    sections: List[Dict[str, str]] = Field(default_factory=list)
    analysis: Optional[DocumentAnalysisResult] = None
    
    # Generation metadata
    generation_time: Optional[float] = None
    model_used: Optional[str] = None
    token_usage: Optional[Dict[str, int]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "response_file": {
                    "name": "response_topaza_20240115_1200_tender.docx",
                    "path": "/ai_responses/response_topaza_20240115_1200_tender.docx",
                    "size": 45678,
                    "created_at": "2024-01-15T12:00:00Z"
                },
                "sections": [
                    {"title": "Introduction", "content": "Detailed introduction..."},
                    {"title": "Methodology", "content": "Our approach..."}
                ],
                "generation_time": 15.2,
                "model_used": "gpt-4-turbo"
            }
        }


class ChatResponse(BaseModel):
    """Chat response"""
    answer: str
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    sources: List[str] = Field(default_factory=list)
    
    # Response metadata
    processing_time: Optional[float] = None
    model_used: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "answer": "Based on the document, the main requirements include...",
                "confidence": 0.88,
                "sources": ["Section 3.1", "Annex A"],
                "processing_time": 1.2,
                "model_used": "gpt-4-turbo"
            }
        }


class AIStatusResponse(BaseResponse):
    """AI processing status"""
    operation: Optional[AIOperation] = None
    progress: int = Field(0, ge=0, le=100)
    current_step: Optional[str] = None
    estimated_time_remaining: Optional[float] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "processing",
                "operation": "response_generation",
                "progress": 60,
                "current_step": "Generating methodology section",
                "estimated_time_remaining": 30.0
            }
        }


class GeneratedFilesResponse(BaseResponse):
    """Generated files list response"""
    files: List[FileInfo] = Field(default_factory=list)
    total_files: int = 0
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "files": [],
                "total_files": 5
            }
        }


class ReportConfiguration(BaseModel):
    """Report generation configuration matching frontend"""
    report_type: ReportType = Field(..., description="Type of report to generate")
    tone: ReportTone = Field(ReportTone.PROFESSIONAL, description="Writing tone for the report")
    length: ReportLength = Field(ReportLength.DETAILED, description="Target length for the report")
    custom_instructions: Optional[str] = Field(None, max_length=2000, description="Additional instructions or focus areas")
    
    class Config:
        json_schema_extra = {
            "example": {
                "report_type": "proposal",
                "tone": "professional",
                "length": "detailed",
                "custom_instructions": "Focus on technical capabilities and competitive advantages"
            }
        }


class AIReportRequest(BaseModel):
    """AI report generation request matching frontend expectations exactly"""
    tenderId: str = Field(..., description="ID of the tender to generate report for")
    reportType: ReportType = Field(ReportType.PROPOSAL, description="Type of report")
    tone: ReportTone = Field(ReportTone.PROFESSIONAL, description="Tone of report")
    length: ReportLength = Field(ReportLength.DETAILED, description="Length of report")
    customInstructions: Optional[str] = Field(None, description="Custom instructions")
    
    @field_validator('customInstructions')
    @classmethod
    def validate_custom_instructions(cls, v):
        if v and len(v) > 2000:
            raise ValueError("Custom instructions must be 2000 characters or less")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "tenderId": "abc123",
                "reportType": "proposal",
                "tone": "professional", 
                "length": "detailed",
                "customInstructions": "Emphasize our technical expertise in renewable energy projects"
            }
        }


class ReportGenerationResponse(BaseModel):
    """Report generation response with full content for frontend display"""
    report_id: str = Field(..., description="Unique identifier for the generated report")
    status: str = Field(..., description="Generation status (completed, failed, processing)")
    content: str = Field(..., description="Full markdown content of the generated report")
    download_url: Optional[str] = Field(None, description="URL to download the report as DOCX")
    
    # Metadata that frontend expects
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Report metadata")
    generation_time: Optional[float] = Field(None, description="Time taken to generate in seconds")
    word_count: Optional[int] = Field(None, description="Word count of generated report")
    page_count: Optional[int] = Field(None, description="Estimated page count")
    sections_count: Optional[int] = Field(None, description="Number of sections generated")
    
    class Config:
        json_schema_extra = {
            "example": {
                "report_id": "rpt_abc123_20241215",
                "status": "completed",
                "download_url": "/api/v1/ai/download/report_abc123.docx",
                "preview_content": "Executive Summary: This proposal outlines...",
                "metadata": {
                    "report_type": "proposal",
                    "tone": "professional",
                    "length": "detailed"
                },
                "generation_time": 45.2,
                "word_count": 2500,
                "page_count": 5
            }
        }