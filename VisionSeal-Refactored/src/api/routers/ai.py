"""
AI router with secure file handling
Secure replacement for AI endpoints from monolithic main.py
"""
import os
import tempfile
from pathlib import Path
from typing import Dict, Any, List
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse

from ..schemas.ai import (
    ChatRequest,
    DocumentAnalysisRequest,
    ChatResponse,
    DocumentAnalysisResult,
    ResponseGenerationResult,
    GeneratedFilesResponse,
    AIStatusResponse
)
from ..schemas.common import SuccessResponse, FileInfo
from ...core.security.auth import auth_manager
from ...core.security.validators import FileValidator, PathValidator
from ...core.exceptions.handlers import AIProcessingException, SecurityException
from ...core.config.settings import settings
from ...core.logging.setup import get_logger

logger = get_logger("ai")
router = APIRouter(prefix="/ai", tags=["ai"])


class AIService:
    """Secure AI processing service"""
    
    def __init__(self):
        self.processing_sessions: Dict[str, Dict[str, Any]] = {}
    
    async def analyze_document(
        self,
        file: UploadFile,
        request: DocumentAnalysisRequest,
        user: Dict[str, Any]
    ) -> DocumentAnalysisResult:
        """Analyze uploaded document with security validation"""
        try:
            # Validate file upload
            FileValidator.validate_file_upload(file)
            
            # Create secure temporary file
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=Path(file.filename).suffix,
                dir=settings.uploads_dir / "temp"
            ) as temp_file:
                
                # Read and save file securely
                content = await file.read()
                temp_file.write(content)
                temp_file_path = temp_file.name
            
            try:
                logger.info(
                    "Starting document analysis",
                    extra={
                        "filename": file.filename,
                        "file_size": len(content),
                        "user_id": user.get("user_id"),
                        "operation": request.operation.value
                    }
                )
                
                # TODO: Implement actual AI analysis
                # For now, return mock analysis
                result = DocumentAnalysisResult(
                    summary="Document analysis completed successfully",
                    key_points=["Mock analysis result"],
                    processing_time=2.5,
                    model_used="gpt-4-turbo"
                )
                
                logger.info("Document analysis completed successfully")
                return result
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except OSError:
                    logger.warning(f"Failed to delete temporary file: {temp_file_path}")
                
        except Exception as e:
            logger.error(f"Document analysis failed: {str(e)}")
            raise AIProcessingException(f"Document analysis failed: {str(e)}")
    
    async def generate_response(
        self,
        file: UploadFile,
        user: Dict[str, Any]
    ) -> ResponseGenerationResult:
        """Generate AI response for tender document"""
        try:
            # Validate file upload
            FileValidator.validate_file_upload(file)
            
            # Create secure file path
            secure_filename = FileValidator.sanitize_filename(file.filename)
            if not secure_filename:
                raise SecurityException("Invalid filename")
            
            file_path = settings.uploads_dir / secure_filename
            
            # Save file securely
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            try:
                logger.info(
                    "Starting response generation",
                    extra={
                        "filename": secure_filename,
                        "file_size": len(content),
                        "user_id": user.get("user_id")
                    }
                )
                
                # TODO: Implement actual response generation
                # For now, return mock result
                
                # Create mock response file info
                response_filename = f"response_{secure_filename}_{user.get('user_id', 'unknown')}.docx"
                response_path = settings.data_dir / "ai_responses" / response_filename
                
                result = ResponseGenerationResult(
                    response_file=FileInfo(
                        name=response_filename,
                        path=str(response_path),
                        size=12345,
                        created_at=datetime.utcnow()
                    ),
                    sections=[
                        {"title": "Introduction", "content": "Mock introduction"},
                        {"title": "Methodology", "content": "Mock methodology"}
                    ],
                    generation_time=15.2,
                    model_used="gpt-4-turbo"
                )
                
                logger.info("Response generation completed successfully")
                return result
                
            finally:
                # Clean up uploaded file
                try:
                    os.unlink(file_path)
                except OSError:
                    logger.warning(f"Failed to delete uploaded file: {file_path}")
                
        except Exception as e:
            logger.error(f"Response generation failed: {str(e)}")
            raise AIProcessingException(f"Response generation failed: {str(e)}")
    
    async def process_chat(
        self,
        request: ChatRequest,
        user: Dict[str, Any]
    ) -> ChatResponse:
        """Process chat/Q&A request"""
        try:
            # Validate document path if provided
            if request.document_path:
                PathValidator.validate_file_path(
                    request.document_path,
                    settings.uploads_dir
                )
            
            logger.info(
                "Processing chat request",
                extra={
                    "question_length": len(request.question),
                    "has_document": bool(request.document_path),
                    "user_id": user.get("user_id")
                }
            )
            
            # TODO: Implement actual chat processing
            # For now, return mock response
            response = ChatResponse(
                answer="This is a mock response to your question.",
                confidence=0.85,
                sources=["Document section 1", "Document section 2"],
                processing_time=1.2,
                model_used="gpt-4-turbo"
            )
            
            logger.info("Chat request processed successfully")
            return response
            
        except Exception as e:
            logger.error(f"Chat processing failed: {str(e)}")
            raise AIProcessingException(f"Chat processing failed: {str(e)}")
    
    async def get_generated_files(self, user: Dict[str, Any]) -> List[FileInfo]:
        """Get list of generated files for user"""
        try:
            files = []
            ai_responses_dir = settings.data_dir / "ai_responses"
            
            if ai_responses_dir.exists():
                for file_path in ai_responses_dir.glob("*.docx"):
                    # Filter by user if needed (implement user-specific files)
                    stat = file_path.stat()
                    files.append(FileInfo(
                        name=file_path.name,
                        path=str(file_path),
                        size=stat.st_size,
                        created_at=datetime.fromtimestamp(stat.st_ctime),
                        modified_at=datetime.fromtimestamp(stat.st_mtime)
                    ))
            
            # Sort by creation time (newest first)
            files.sort(key=lambda x: x.created_at, reverse=True)
            
            logger.info(
                "Retrieved generated files",
                extra={
                    "file_count": len(files),
                    "user_id": user.get("user_id")
                }
            )
            
            return files
            
        except Exception as e:
            logger.error(f"Failed to get generated files: {str(e)}")
            raise AIProcessingException(f"Failed to get generated files: {str(e)}")


# Service instance
ai_service = AIService()


@router.post("/analyze", response_model=DocumentAnalysisResult)
async def analyze_document(
    request: DocumentAnalysisRequest = Depends(),
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(auth_manager.get_current_user)
):
    """
    Analyze uploaded document
    
    Secure replacement for document analysis functionality
    """
    return await ai_service.analyze_document(file, request, current_user)


@router.post("/generate", response_model=ResponseGenerationResult)
async def generate_response(
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(auth_manager.get_current_user)
):
    """
    Generate AI response for uploaded tender document
    
    Secure replacement for:
    - /api/ai/generate
    """
    return await ai_service.generate_response(file, current_user)


@router.post("/chat", response_model=ChatResponse)
async def process_chat(
    request: ChatRequest,
    current_user: Dict[str, Any] = Depends(auth_manager.get_current_user)
):
    """
    Process Q&A with document context
    
    Secure replacement for:
    - /api/ai/chat
    """
    return await ai_service.process_chat(request, current_user)


@router.get("/generated-files", response_model=GeneratedFilesResponse)
async def get_generated_files(
    current_user: Dict[str, Any] = Depends(auth_manager.get_current_user)
):
    """
    Get list of generated AI response files
    
    Secure replacement for:
    - /api/ai/generated-files
    """
    try:
        files = await ai_service.get_generated_files(current_user)
        
        return GeneratedFilesResponse(
            status="success",
            files=files,
            total_files=len(files),
            message="Generated files retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to get generated files: {str(e)}")
        raise AIProcessingException(f"Failed to get generated files: {str(e)}")


@router.get("/download/{filename}")
async def download_file(
    filename: str,
    current_user: Dict[str, Any] = Depends(auth_manager.get_current_user)
):
    """
    Download generated AI response file
    
    Secure replacement for file download functionality
    """
    try:
        # Sanitize filename
        secure_filename = FileValidator.sanitize_filename(filename)
        if not secure_filename:
            raise SecurityException("Invalid filename")
        
        # Validate file path
        file_path = PathValidator.validate_file_path(
            secure_filename,
            settings.data_dir / "ai_responses"
        )
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        logger.info(
            "File download requested",
            extra={
                "filename": secure_filename,
                "user_id": current_user.get("user_id")
            }
        )
        
        return FileResponse(
            path=str(file_path),
            filename=secure_filename,
            media_type="application/octet-stream"
        )
        
    except Exception as e:
        logger.error(f"File download failed: {str(e)}")
        raise AIProcessingException(f"File download failed: {str(e)}")


# Add missing import
from datetime import datetime