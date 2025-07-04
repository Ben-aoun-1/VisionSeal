"""
Automation router
Secure replacement for automation endpoints from monolithic main.py
"""
from typing import Dict, Any
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from ..schemas.automation import (
    AutomationStartRequest,
    DeepDiveRequest, 
    AutomationStatusResponse,
    ExtractionResults,
    AutomationSource
)
from ..schemas.common import SuccessResponse, ErrorResponse
from ...core.security.auth import auth_manager
from ...core.security.validators import InputValidator
from ...core.exceptions.handlers import AutomationException, ValidationException
from ...core.logging.setup import get_logger

logger = get_logger("automation")
router = APIRouter(prefix="/automation", tags=["automation"])


class AutomationService:
    """Secure automation service"""
    
    def __init__(self):
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
    
    async def start_automation(
        self,
        request: AutomationStartRequest,
        user: Dict[str, Any]
    ) -> AutomationStatusResponse:
        """Start automation with proper validation"""
        try:
            # Validate source
            source = InputValidator.validate_source_parameter(request.source.value)
            
            logger.info(
                "Starting automation",
                extra={
                    "source": source,
                    "user_id": user.get("user_id"),
                    "max_pages": request.max_pages
                }
            )
            
            # Create session
            import uuid
            session_id = str(uuid.uuid4())
            
            self.active_sessions[session_id] = {
                "source": source,
                "status": "starting",
                "progress": 0,
                "user_id": user.get("user_id"),
                "started_at": "now"
            }
            
            return AutomationStatusResponse(
                status="processing",
                session_id=session_id,
                current_step=f"Initializing {source} automation",
                message=f"Automation started for {source}"
            )
            
        except Exception as e:
            logger.error(f"Failed to start automation: {str(e)}")
            raise AutomationException(f"Failed to start automation: {str(e)}")
    
    async def get_status(
        self,
        source: AutomationSource,
        session_id: str = None
    ) -> AutomationStatusResponse:
        """Get automation status"""
        try:
            # For now, return mock status
            # TODO: Implement actual status tracking
            return AutomationStatusResponse(
                status="completed",
                progress=100,
                current_step="Automation completed",
                items_found=25,
                items_processed=25,
                enhanced=True
            )
            
        except Exception as e:
            logger.error(f"Failed to get status: {str(e)}")
            raise AutomationException(f"Failed to get status: {str(e)}")
    
    async def stop_automation(
        self,
        source: AutomationSource,
        user: Dict[str, Any]
    ) -> SuccessResponse:
        """Stop automation"""
        try:
            logger.info(
                "Stopping automation",
                extra={
                    "source": source.value,
                    "user_id": user.get("user_id")
                }
            )
            
            # TODO: Implement actual stop logic
            
            return SuccessResponse(
                message=f"{source.value} automation stopped successfully"
            )
            
        except Exception as e:
            logger.error(f"Failed to stop automation: {str(e)}")
            raise AutomationException(f"Failed to stop automation: {str(e)}")


# Service instance
automation_service = AutomationService()


@router.post("/start", response_model=AutomationStatusResponse)
async def start_automation(
    request: AutomationStartRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(auth_manager.get_current_user)
):
    """
    Start automation for specified source
    
    Secure replacement for:
    - /api/ungm/start
    - /api/tunipages/start  
    - /api/automation/start-both
    """
    return await automation_service.start_automation(request, current_user)


@router.get("/status/{source}", response_model=AutomationStatusResponse)
async def get_automation_status(
    source: AutomationSource,
    session_id: str = None,
    current_user: Dict[str, Any] = Depends(auth_manager.get_current_user)
):
    """
    Get automation status
    
    Secure replacement for:
    - /api/ungm/status
    - /api/tunipages/status
    - /api/ungm/progress
    """
    return await automation_service.get_status(source, session_id)


@router.post("/stop/{source}", response_model=SuccessResponse)
async def stop_automation(
    source: AutomationSource,
    current_user: Dict[str, Any] = Depends(auth_manager.get_current_user)
):
    """
    Stop automation for specified source
    
    Secure replacement for:
    - /api/ungm/stop
    """
    return await automation_service.stop_automation(source, current_user)


@router.get("/results/{source}", response_model=ExtractionResults)
async def get_extraction_results(
    source: AutomationSource,
    current_user: Dict[str, Any] = Depends(auth_manager.get_current_user)
):
    """
    Get latest extraction results
    
    Secure replacement for:
    - /api/ungm/results
    - /api/tunipages/results
    """
    try:
        logger.info(
            "Getting extraction results",
            extra={
                "source": source.value,
                "user_id": current_user.get("user_id")
            }
        )
        
        # TODO: Implement actual results retrieval
        # For now, return empty results
        return ExtractionResults(
            status="success",
            data=[],
            total_items=0,
            source=source,
            message=f"No {source.value} results available yet"
        )
        
    except Exception as e:
        logger.error(f"Failed to get results: {str(e)}")
        raise AutomationException(f"Failed to get results: {str(e)}")


@router.post("/deep-dive", response_model=AutomationStatusResponse)
async def start_deep_dive(
    request: DeepDiveRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(auth_manager.get_current_user)
):
    """
    Start deep dive extraction for specific tender
    
    Secure replacement for:
    - /api/automation/deep-dive
    """
    try:
        logger.info(
            "Starting deep dive extraction",
            extra={
                "item_id": request.item_id,
                "source": request.source.value,
                "user_id": current_user.get("user_id")
            }
        )
        
        # Create session for deep dive
        import uuid
        session_id = str(uuid.uuid4())
        
        # TODO: Implement actual deep dive logic
        
        return AutomationStatusResponse(
            status="processing",
            session_id=session_id,
            current_step=f"Starting deep dive for {request.source.value} item",
            message=f"Deep dive extraction started for item {request.item_id}"
        )
        
    except Exception as e:
        logger.error(f"Failed to start deep dive: {str(e)}")
        raise AutomationException(f"Failed to start deep dive: {str(e)}")


@router.get("/capabilities", response_model=SuccessResponse)
async def get_automation_capabilities(
    current_user: Dict[str, Any] = Depends(auth_manager.get_current_user)
):
    """
    Get automation capabilities status
    
    Secure replacement for:
    - /api/automation/enhanced-status
    """
    try:
        return SuccessResponse(
            data={
                "enhanced_available": True,
                "sources": ["ungm", "tunipages"],
                "features": [
                    "Smart authentication with discovered selectors",
                    "Enhanced table extraction using site structure analysis", 
                    "Document discovery and detail page extraction",
                    "Relevance scoring for opportunities",
                    "Cross-platform analytics and reporting"
                ],
                "security_features": [
                    "Input validation and sanitization",
                    "Rate limiting and request throttling",
                    "Secure file handling",
                    "Authentication and authorization"
                ]
            },
            message="Automation capabilities retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to get capabilities: {str(e)}")
        raise AutomationException(f"Failed to get capabilities: {str(e)}")