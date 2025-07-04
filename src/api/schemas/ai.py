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
        schema_extra = {
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
        schema_extra = {
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
        schema_extra = {
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
        schema_extra = {
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
        schema_extra = {
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
        schema_extra = {
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
        schema_extra = {
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
        schema_extra = {
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
        schema_extra = {
            "example": {
                "status": "success",
                "files": [],
                "total_files": 5
            }
        }