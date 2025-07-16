"""
Clean Automation Router
Simplified, readable automation endpoints using the new service architecture
"""
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from automation.manager import automation_manager
from automation.constants import TaskPriority, TaskStatus
from core.auth.supabase_auth import get_current_user
from api.schemas.common import SuccessResponse
from core.logging.setup import get_logger

logger = get_logger("automation_router")
router = APIRouter(prefix="/automation", tags=["automation"])


# === Request Models ===

class StartScrapingRequest(BaseModel):
    """Request to start scraping"""
    source: str = Field(..., description="Scraper source (ungm, tunipages)")
    max_pages: Optional[int] = Field(10, description="Maximum pages to scrape")
    priority: Optional[str] = Field("high", description="Task priority")
    profile: Optional[str] = Field(None, description="Configuration profile")
    
    class Config:
        json_schema_extra = {
            "example": {
                "source": "ungm",
                "max_pages": 10,
                "priority": "high",
                "profile": "topaza_africa"
            }
        }


class SessionStatusResponse(BaseModel):
    """Response for session status"""
    session_id: str
    status: str
    source: str
    tenders_found: int
    tenders_processed: int
    progress_percent: float
    start_time: Optional[str]
    duration_seconds: Optional[float]
    error_message: Optional[str]


# === Core Automation Endpoints ===

@router.post("/start", response_model=SuccessResponse)
async def start_scraping(
    request: StartScrapingRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Start a new scraping session
    
    This endpoint creates and starts a scraping session for the specified source.
    """
    try:
        logger.info(f"Starting scraping for {request.source} (user: {current_user['user_id']})")
        
        # Validate source
        available_scrapers = automation_manager.get_available_scrapers()
        if request.source not in available_scrapers:
            raise HTTPException(
                status_code=400,
                detail=f"Scraper '{request.source}' not available. Available: {available_scrapers}"
            )
        
        # Convert priority string to enum
        priority_map = {
            "low": TaskPriority.LOW,
            "medium": TaskPriority.MEDIUM, 
            "high": TaskPriority.HIGH,
            "urgent": TaskPriority.URGENT
        }
        priority = priority_map.get(request.priority.lower(), TaskPriority.HIGH)
        
        # Prepare configuration
        config = {
            "max_pages": request.max_pages,
            "user_id": current_user["user_id"]
        }
        
        # Start scraping
        session_id = automation_manager.start_scraping(
            source=request.source,
            user_id=current_user["user_id"],
            config=config,
            priority=priority,
            profile=request.profile
        )
        
        if not session_id:
            raise HTTPException(status_code=500, detail="Failed to start scraping session")
        
        return SuccessResponse(
            data={
                "session_id": session_id,
                "source": request.source,
                "status": "started"
            },
            message=f"Scraping started for {request.source}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start scraping: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start scraping: {str(e)}")


@router.get("/status/{session_id}", response_model=SessionStatusResponse)
async def get_session_status(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get the status of a specific scraping session
    """
    try:
        status_data = automation_manager.get_session_status(session_id)
        
        if 'error' in status_data:
            raise HTTPException(status_code=404, detail=status_data['error'])
        
        # Calculate progress percentage
        progress = 0.0
        if status_data['status'] == 'completed':
            progress = 100.0
        elif status_data['status'] == 'running':
            progress = 50.0  # Rough estimate
        elif status_data['status'] == 'failed':
            progress = 0.0
        
        return SessionStatusResponse(
            session_id=session_id,
            status=status_data['status'],
            source=status_data['source'],
            tenders_found=status_data['tenders_found'],
            tenders_processed=status_data['tenders_processed'],
            progress_percent=progress,
            start_time=status_data['start_time'],
            duration_seconds=status_data['duration_seconds'],
            error_message=status_data['error_message']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get session status: {str(e)}")


@router.post("/cancel/{session_id}", response_model=SuccessResponse)
async def cancel_session(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Cancel a running scraping session
    """
    try:
        success = automation_manager.cancel_session(session_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Session not found or cannot be cancelled")
        
        return SuccessResponse(
            message=f"Session {session_id} cancelled successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel session: {str(e)}")


# === Session Management ===

@router.get("/sessions", response_model=SuccessResponse)
async def list_sessions(
    source: Optional[str] = None,
    status: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    List scraping sessions for the current user
    """
    try:
        # Convert status string to enum if provided
        status_filter = None
        if status:
            try:
                status_filter = TaskStatus(status.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        sessions = automation_manager.list_sessions(
            user_id=current_user["user_id"],
            source=source,
            status=status_filter
        )
        
        return SuccessResponse(
            data={
                "sessions": sessions,
                "total": len(sessions)
            },
            message=f"Found {len(sessions)} sessions"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list sessions: {str(e)}")


@router.post("/start-all", response_model=SuccessResponse)
async def start_all_scrapers(
    max_pages: Optional[int] = 10,
    priority: Optional[str] = "high",
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Start scraping sessions for all available scrapers
    """
    try:
        # Convert priority
        priority_map = {
            "low": TaskPriority.LOW,
            "medium": TaskPriority.MEDIUM,
            "high": TaskPriority.HIGH,
            "urgent": TaskPriority.URGENT
        }
        task_priority = priority_map.get(priority.lower(), TaskPriority.HIGH)
        
        # Configuration for all scrapers
        config = {
            "max_pages": max_pages,
            "user_id": current_user["user_id"]
        }
        
        session_ids = automation_manager.start_all_scrapers(config)
        
        return SuccessResponse(
            data={
                "session_ids": session_ids,
                "total_started": len(session_ids)
            },
            message=f"Started {len(session_ids)} scraping sessions"
        )
        
    except Exception as e:
        logger.error(f"Failed to start all scrapers: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start all scrapers: {str(e)}")


# === System Information ===

@router.get("/capabilities", response_model=SuccessResponse)
async def get_capabilities(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get automation system capabilities and available scrapers
    """
    try:
        capabilities = automation_manager.get_scraper_capabilities()
        
        return SuccessResponse(
            data=capabilities,
            message="Automation capabilities retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to get capabilities: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get capabilities: {str(e)}")


@router.get("/health", response_model=SuccessResponse)
async def get_system_health(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get automation system health status
    """
    try:
        health_summary = automation_manager.get_health_summary()
        
        return SuccessResponse(
            data=health_summary,
            message=f"System is {health_summary['status']}"
        )
        
    except Exception as e:
        logger.error(f"Failed to get system health: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get system health: {str(e)}")


@router.get("/metrics", response_model=SuccessResponse)
async def get_system_metrics(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get comprehensive system metrics and performance data
    """
    try:
        metrics = automation_manager.get_metrics()
        
        return SuccessResponse(
            data=metrics,
            message="System metrics retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to get metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@router.get("/performance", response_model=SuccessResponse)
async def get_performance_report(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get detailed performance analysis and recommendations
    """
    try:
        report = automation_manager.get_performance_report()
        
        return SuccessResponse(
            data=report,
            message="Performance report generated successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to get performance report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get performance report: {str(e)}")


# === Administrative Endpoints ===

@router.post("/cleanup", response_model=SuccessResponse)
async def cleanup_old_data(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Clean up old tasks and sessions (admin operation)
    """
    try:
        # Note: In a real system, you might want to check for admin role here
        cleanup_result = automation_manager.cleanup_old_data()
        
        return SuccessResponse(
            data=cleanup_result,
            message=f"Cleaned up {cleanup_result['total_cleaned']} old records"
        )
        
    except Exception as e:
        logger.error(f"Failed to cleanup old data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to cleanup old data: {str(e)}")


@router.post("/restart", response_model=SuccessResponse)
async def restart_services(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Restart automation services (admin operation)
    """
    try:
        # Note: In a real system, you might want to check for admin role here
        success = automation_manager.restart_services()
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to restart services")
        
        return SuccessResponse(
            message="Automation services restarted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to restart services: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to restart services: {str(e)}")