"""
Automation API Routes for VisionSeal
Provides endpoints for managing background automation tasks
"""
from typing import Dict, List, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field

from automation.task_manager import automation_manager, TaskPriority
from core.logging.setup import get_logger

logger = get_logger("automation_api")

router = APIRouter(prefix="/automation", tags=["automation"])


class ScrapingSessionRequest(BaseModel):
    """Request to start a scraping session"""
    source: str = Field(..., description="Scraper source (ungm, tunipages)")
    config: Optional[Dict[str, Any]] = Field(None, description="Scraper configuration")
    priority: str = Field("medium", description="Task priority (low, medium, high, urgent)")


class ScrapingSessionResponse(BaseModel):
    """Response for scraping session"""
    task_id: str
    source: str
    status: str
    message: str


class SessionStatusResponse(BaseModel):
    """Response for session status"""
    task_id: str
    name: str
    status: str
    source: Optional[str]
    created_at: datetime
    last_attempt: Optional[datetime]
    retry_count: int
    result: Optional[Dict[str, Any]]


class AutomationMetrics(BaseModel):
    """Automation system metrics"""
    tasks_created: int
    tasks_completed: int
    tasks_failed: int
    tasks_retried: int
    active_tasks: int
    pending_tasks: int
    retrying_tasks: int
    total_tasks: int
    average_execution_time: float


def get_task_priority(priority_str: str) -> TaskPriority:
    """Convert string priority to TaskPriority enum"""
    priority_map = {
        'low': TaskPriority.LOW,
        'medium': TaskPriority.MEDIUM,
        'high': TaskPriority.HIGH,
        'urgent': TaskPriority.URGENT
    }
    return priority_map.get(priority_str.lower(), TaskPriority.MEDIUM)


@router.post("/sessions", response_model=ScrapingSessionResponse)
async def start_scraping_session(request: ScrapingSessionRequest):
    """Start a new scraping session"""
    try:
        priority = get_task_priority(request.priority)
        
        task_id = automation_manager.schedule_scraping_session(
            source=request.source,
            config=request.config,
            priority=priority
        )
        
        if not task_id:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to schedule scraping session for source: {request.source}"
            )
        
        logger.info(f"Started scraping session {task_id} for {request.source}")
        
        return ScrapingSessionResponse(
            task_id=task_id,
            source=request.source,
            status="scheduled",
            message=f"Scraping session scheduled successfully for {request.source}"
        )
        
    except Exception as e:
        logger.error(f"Failed to start scraping session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/all", response_model=List[ScrapingSessionResponse])
async def start_all_scraping_sessions(
    config: Optional[Dict[str, Any]] = None,
    priority: str = "high"
):
    """Start scraping sessions for all available sources"""
    try:
        task_priority = get_task_priority(priority)
        task_ids = automation_manager.schedule_all_scrapers(config)
        
        responses = []
        for task_id in task_ids:
            # Get task info to determine source
            session_info = automation_manager.get_session_status(task_id)
            source = session_info.get('task_info', {}).metadata.get('source', 'unknown')
            
            responses.append(ScrapingSessionResponse(
                task_id=task_id,
                source=source,
                status="scheduled",
                message=f"Scraping session scheduled for {source}"
            ))
        
        logger.info(f"Started {len(task_ids)} scraping sessions")
        return responses
        
    except Exception as e:
        logger.error(f"Failed to start all scraping sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{task_id}", response_model=SessionStatusResponse)
async def get_session_status(task_id: str):
    """Get status of a specific scraping session"""
    try:
        session_info = automation_manager.get_session_status(task_id)
        
        if not session_info['status']:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        task_info = session_info['task_info']
        result_data = None
        
        if session_info['result']:
            result_data = {
                'status': session_info['result'].status.value,
                'execution_time': session_info['result'].execution_time,
                'started_at': session_info['result'].started_at,
                'completed_at': session_info['result'].completed_at,
                'error': session_info['result'].error,
                'metadata': session_info['result'].metadata
            }
        
        return SessionStatusResponse(
            task_id=task_id,
            name=task_info.name,
            status=session_info['status'],
            source=task_info.metadata.get('source'),
            created_at=task_info.created_at,
            last_attempt=task_info.last_attempt,
            retry_count=task_info.retry_count,
            result=result_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions", response_model=List[SessionStatusResponse])
async def list_all_sessions():
    """List all scraping sessions"""
    try:
        sessions = automation_manager.get_all_sessions()
        
        response_sessions = []
        for session in sessions:
            # Get detailed status for each session
            session_info = automation_manager.get_session_status(session['task_id'])
            result_data = None
            
            if session_info['result']:
                result_data = {
                    'status': session_info['result'].status.value,
                    'execution_time': session_info['result'].execution_time,
                    'started_at': session_info['result'].started_at,
                    'completed_at': session_info['result'].completed_at,
                    'error': session_info['result'].error,
                    'metadata': session_info['result'].metadata
                }
            
            response_sessions.append(SessionStatusResponse(
                task_id=session['task_id'],
                name=session['name'],
                status=session['status'],
                source=session['source'],
                created_at=session['created_at'],
                last_attempt=session['last_attempt'],
                retry_count=session['retry_count'],
                result=result_data
            ))
        
        return response_sessions
        
    except Exception as e:
        logger.error(f"Failed to list sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sessions/{task_id}")
async def cancel_session(task_id: str):
    """Cancel a running or pending scraping session"""
    try:
        success = automation_manager.cancel_session(task_id)
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail=f"Could not cancel task {task_id} (may not exist or already completed)"
            )
        
        logger.info(f"Cancelled scraping session {task_id}")
        return {"message": f"Task {task_id} cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics", response_model=AutomationMetrics)
async def get_automation_metrics():
    """Get automation system metrics"""
    try:
        metrics = automation_manager.get_metrics()
        
        return AutomationMetrics(
            tasks_created=metrics['tasks_created'],
            tasks_completed=metrics['tasks_completed'],
            tasks_failed=metrics['tasks_failed'],
            tasks_retried=metrics['tasks_retried'],
            active_tasks=metrics['active_tasks'],
            pending_tasks=metrics['pending_tasks'],
            retrying_tasks=metrics['retrying_tasks'],
            total_tasks=metrics['total_tasks'],
            average_execution_time=metrics['average_execution_time']
        )
        
    except Exception as e:
        logger.error(f"Failed to get metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/health-check")
async def automation_health_check():
    """Check automation system health"""
    try:
        metrics = automation_manager.get_metrics()
        
        # Basic health checks
        health_status = {
            'status': 'healthy',
            'task_manager_running': True,
            'active_tasks': metrics['active_tasks'],
            'pending_tasks': metrics['pending_tasks'],
            'failed_tasks_ratio': metrics['tasks_failed'] / max(metrics['tasks_created'], 1),
            'issues': []
        }
        
        # Check for potential issues
        if metrics['active_tasks'] > 10:
            health_status['issues'].append('High number of active tasks')
        
        if health_status['failed_tasks_ratio'] > 0.5:
            health_status['issues'].append('High failure rate')
            health_status['status'] = 'degraded'
        
        if metrics['retrying_tasks'] > 5:
            health_status['issues'].append('Many tasks retrying')
            health_status['status'] = 'degraded'
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            'status': 'unhealthy',
            'error': str(e),
            'task_manager_running': False
        }