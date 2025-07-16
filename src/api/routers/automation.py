"""
Automation router
Secure replacement for automation endpoints from monolithic main.py
Enhanced with background task management
"""
from typing import Dict, Any, List
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from api.schemas.automation import (
    AutomationStartRequest,
    DeepDiveRequest, 
    AutomationStatusResponse,
    ExtractionResults,
    AutomationSource
)
from api.schemas.common import SuccessResponse, ErrorResponse
from automation.task_manager import automation_manager, TaskPriority
from core.auth.supabase_auth import get_current_user, get_current_user_optional
from core.security.validators import InputValidator
from core.exceptions.handlers import AutomationException, ValidationException
from core.logging.setup import get_logger

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
            
            # Handle optional user (for development/testing)
            user_id = user.get("user_id") if user else "anonymous"
            
            logger.info(
                "Starting automation",
                extra={
                    "source": source,
                    "user_id": user_id,
                    "max_pages": request.max_pages
                }
            )
            
            # Create configuration for the scraper
            config = {
                'max_pages': request.max_pages,
                'headless': True,  # Always run headless in production
                'user_id': user_id
            }
            
            # Schedule scraping session using task manager
            task_id = automation_manager.schedule_scraping_session(
                source=source,
                config=config,
                priority=TaskPriority.HIGH
            )
            
            if not task_id:
                raise AutomationException(f"Failed to schedule scraping session for {source}")
            
            # Store session mapping
            self.active_sessions[task_id] = {
                "source": source,
                "status": "starting",
                "progress": 0,
                "user_id": user_id,
                "started_at": "now",
                "task_id": task_id
            }
            
            return AutomationStatusResponse(
                status="processing",
                session_id=task_id,
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
            if session_id:
                # Get status from task manager
                session_info = automation_manager.get_session_status(session_id)
                
                if not session_info['status']:
                    raise AutomationException(f"Session {session_id} not found")
                
                task_info = session_info['task_info']
                result = session_info['result']
                
                # Map task status to automation status
                status_mapping = {
                    'pending': 'waiting',
                    'running': 'processing',
                    'completed': 'completed',
                    'failed': 'error',
                    'cancelled': 'stopped',
                    'retrying': 'processing'
                }
                
                status = status_mapping.get(session_info['status'], 'unknown')
                
                # Calculate progress based on task state
                progress = 0
                if session_info['status'] == 'running':
                    progress = 50  # Assume 50% when running
                elif session_info['status'] == 'completed':
                    progress = 100
                elif session_info['status'] == 'failed':
                    progress = 0
                
                # Get items found/processed from result
                items_found = 0
                items_processed = 0
                if result and result.result:
                    items_found = result.result.get('tenders_found', 0)
                    items_processed = result.result.get('tenders_processed', 0)
                
                return AutomationStatusResponse(
                    status=status,
                    session_id=session_id,
                    progress=progress,
                    current_step=f"{source.value} automation {session_info['status']}",
                    items_found=items_found,
                    items_processed=items_processed,
                    enhanced=True,
                    message=f"Session {session_id} is {session_info['status']}"
                )
            else:
                # Return general status for source
                return AutomationStatusResponse(
                    status="ready",
                    progress=0,
                    current_step="Ready to start automation",
                    enhanced=True
                )
            
        except Exception as e:
            logger.error(f"Failed to get status: {str(e)}")
            raise AutomationException(f"Failed to get status: {str(e)}")
    
    async def stop_automation(
        self,
        source: AutomationSource,
        user: Dict[str, Any],
        session_id: str = None
    ) -> SuccessResponse:
        """Stop automation"""
        try:
            logger.info(
                "Stopping automation",
                extra={
                    "source": source.value,
                    "user_id": user.get("user_id"),
                    "session_id": session_id
                }
            )
            
            if session_id:
                # Cancel specific session
                success = automation_manager.cancel_session(session_id)
                if not success:
                    raise AutomationException(f"Could not cancel session {session_id}")
                
                # Remove from active sessions
                if session_id in self.active_sessions:
                    del self.active_sessions[session_id]
                
                return SuccessResponse(
                    message=f"Session {session_id} cancelled successfully"
                )
            else:
                # Cancel all sessions for this source
                cancelled_count = 0
                for sid, session in list(self.active_sessions.items()):
                    if session.get("source") == source.value:
                        if automation_manager.cancel_session(sid):
                            del self.active_sessions[sid]
                            cancelled_count += 1
                
                return SuccessResponse(
                    message=f"Cancelled {cancelled_count} {source.value} automation sessions"
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
    current_user: Dict[str, Any] = Depends(get_current_user_optional)
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
    current_user: Dict[str, Any] = Depends(get_current_user_optional)
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
    session_id: str = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Stop automation for specified source
    
    Secure replacement for:
    - /api/ungm/stop
    """
    return await automation_service.stop_automation(source, current_user, session_id)


@router.get("/results/{source}", response_model=ExtractionResults)
async def get_extraction_results(
    source: AutomationSource,
    session_id: str = None,
    limit: int = 50,
    current_user: Dict[str, Any] = Depends(get_current_user)
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
                "session_id": session_id,
                "limit": limit,
                "user_id": current_user.get("user_id")
            }
        )
        
        # Import here to avoid circular imports
        from core.database.supabase_client import supabase_manager
        from datetime import datetime, timedelta
        
        # Determine time range for results
        if session_id:
            # Get results for specific session
            session_info = automation_manager.get_session_status(session_id)
            if not session_info['status']:
                return ExtractionResults(
                    status="success",
                    data=[],
                    total_items=0,
                    source=source,
                    session_id=session_id,
                    message=f"Session {session_id} not found"
                )
            
            # Get session time range
            session_task = session_info.get('task_info')
            if session_task and hasattr(session_task, 'created_at'):
                start_time = session_task.created_at
                end_time = session_task.updated_at or datetime.now()
            else:
                # Fallback to recent results
                start_time = datetime.now() - timedelta(hours=1)
                end_time = datetime.now()
        else:
            # Get recent results (last 24 hours)
            start_time = datetime.now() - timedelta(hours=24)
            end_time = datetime.now()
        
        # Query Supabase for tenders from this source in the time range
        try:
            client = supabase_manager.get_client()
            
            # Build query for tenders from specific source
            # Handle both uppercase and lowercase source values
            source_values = [source.value.upper(), source.value.lower(), source.value.title()]
            
            query = client.table('tenders')\
                .select('*')\
                .in_('source', source_values)\
                .gte('created_at', start_time.isoformat())\
                .lte('created_at', end_time.isoformat())\
                .order('created_at', desc=True)\
                .limit(limit)
            
            response = query.execute()
            tenders_data = response.data if response.data else []
            
            # If no results in time range, get recent tenders from this source
            if not tenders_data and not session_id:
                logger.info(f"No tenders found in time range, querying recent {source.value} tenders")
                recent_query = client.table('tenders')\
                    .select('*')\
                    .in_('source', source_values)\
                    .order('created_at', desc=True)\
                    .limit(limit)
                
                recent_response = recent_query.execute()
                tenders_data = recent_response.data if recent_response.data else []
            
        except Exception as db_error:
            logger.warning(f"Database query failed, falling back to recent tenders: {str(db_error)}")
            # Fallback to general recent tenders query
            tenders_data = await supabase_manager.get_recent_tenders(limit=limit)
            # Filter by source (case insensitive)
            tenders_data = [
                t for t in tenders_data 
                if t.get('source', '').lower() == source.value.lower()
            ]
        
        # Transform database records to TenderInfo format
        tender_results = []
        for tender_record in tenders_data:
            try:
                # Create TenderInfo object from database record
                tender_info = _transform_db_record_to_tender_info(tender_record, source.value)
                tender_results.append(tender_info)
            except Exception as transform_error:
                logger.warning(f"Failed to transform tender record: {str(transform_error)}")
                continue
        
        # Get extraction metadata if we have a session
        extraction_time = None
        result_session_id = session_id
        
        if session_id and session_info.get('result'):
            result = session_info['result']
            if hasattr(result, 'created_at'):
                extraction_time = result.created_at
        elif not session_id and tender_results:
            # Use the most recent tender's creation time
            extraction_time = datetime.fromisoformat(tender_results[0].get('extracted_at', datetime.now().isoformat()))
        
        return ExtractionResults(
            status="success",
            data=tender_results,
            total_items=len(tender_results),
            source=source,
            session_id=result_session_id,
            extraction_time=extraction_time,
            message=f"Found {len(tender_results)} {source.value} results" + 
                   (f" for session {session_id}" if session_id else " from recent extractions")
        )
        
    except Exception as e:
        logger.error(f"Failed to get results: {str(e)}")
        raise AutomationException(f"Failed to get results: {str(e)}")


def _transform_db_record_to_tender_info(record: Dict[str, Any], source: str) -> Dict[str, Any]:
    """Transform database record to TenderInfo format"""
    from datetime import datetime
    
    try:
        # Handle date fields safely
        def safe_date_parse(date_str):
            if not date_str:
                return None
            try:
                if isinstance(date_str, str):
                    return datetime.fromisoformat(date_str.replace('Z', '+00:00')).date()
                return date_str.date() if hasattr(date_str, 'date') else date_str
            except (ValueError, AttributeError):
                return None
        
        # Map database fields to TenderInfo schema
        tender_info = {
            "id": record.get('id', ''),
            "title": record.get('title', ''),
            "source": record.get('source', source).upper(),
            "country": record.get('country'),
            "organization": record.get('organization'),
            "published": safe_date_parse(record.get('publication_date')),
            "deadline": safe_date_parse(record.get('deadline')),
            "status": record.get('status', 'active').lower(),
            "url": record.get('url'),
            "description": record.get('description'),
            "budget": record.get('estimated_budget'),
            "currency": record.get('currency'),
            
            # Enhanced fields
            "details_extracted": record.get('details_extracted', False),
            "documents_found": record.get('documents_found', 0),
            "enhanced": record.get('enhanced', False),
            "is_starred": False,  # Could be added later
            "can_deep_dive": True,
            "relevance_score": float(record.get('relevance_score', 0)) / 100.0 if record.get('relevance_score') else None,
            
            # Additional metadata
            "extracted_at": record.get('extracted_at') or record.get('created_at'),
            "reference": record.get('reference'),
            "notice_type": record.get('notice_type'),
            "contact_email": record.get('contact_email')
        }
        
        # Remove None values for cleaner response
        return {k: v for k, v in tender_info.items() if v is not None}
        
    except Exception as e:
        logger.error(f"Error transforming tender record: {str(e)}")
        # Return minimal valid structure
        return {
            "id": record.get('id', 'unknown'),
            "title": record.get('title', 'Unknown Title'),
            "source": source.upper(),
            "status": "active",
            "can_deep_dive": True
        }


@router.post("/deep-dive", response_model=AutomationStatusResponse)
async def start_deep_dive(
    request: DeepDiveRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_user)
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


@router.get("/health")
async def automation_health_check():
    """Health check for automation API"""
    try:
        # Test automation manager availability
        from automation.task_manager import automation_manager
        metrics = automation_manager.get_metrics()
        return {
            "status": "healthy",
            "service": "automation",
            "task_manager": "available",
            "active_tasks": metrics.get('active_tasks', 0),
            "timestamp": "now"
        }
    except Exception as e:
        return {
            "status": "degraded",
            "service": "automation",
            "error": str(e),
            "timestamp": "now"
        }

@router.get("/capabilities", response_model=SuccessResponse)
async def get_automation_capabilities():
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


@router.post("/sessions/all", response_model=List[AutomationStatusResponse])
async def start_all_sessions(
    max_pages: int = 5,
    priority: str = "high",
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Start automation sessions for all available sources
    """
    try:
        logger.info(
            "Starting all automation sessions",
            extra={
                "user_id": current_user.get("user_id"),
                "max_pages": max_pages,
                "priority": priority
            }
        )
        
        config = {
            'max_pages': max_pages,
            'headless': True,
            'user_id': current_user.get("user_id")
        }
        
        # Schedule all scrapers
        task_ids = automation_manager.schedule_all_scrapers(config)
        
        responses = []
        for task_id in task_ids:
            # Get task info to determine source
            session_info = automation_manager.get_session_status(task_id)
            source = session_info.get('task_info', {}).metadata.get('source', 'unknown')
            
            # Store session
            automation_service.active_sessions[task_id] = {
                "source": source,
                "status": "starting",
                "progress": 0,
                "user_id": current_user.get("user_id"),
                "started_at": "now",
                "task_id": task_id
            }
            
            responses.append(AutomationStatusResponse(
                status="processing",
                session_id=task_id,
                current_step=f"Initializing {source} automation",
                message=f"Automation started for {source}"
            ))
        
        logger.info(f"Started {len(task_ids)} automation sessions")
        return responses
        
    except Exception as e:
        logger.error(f"Failed to start all sessions: {str(e)}")
        raise AutomationException(f"Failed to start all sessions: {str(e)}")


@router.get("/sessions", response_model=List[AutomationStatusResponse])
async def list_all_sessions():
    """
    List all automation sessions
    """
    try:
        sessions = automation_manager.get_all_sessions()
        
        responses = []
        for session in sessions:
            try:
                # Get detailed status - handle potential async issues
                session_info = automation_manager.get_session_status(session['task_id'])
                
                # Ensure session_info is a dict, not a coroutine
                if not isinstance(session_info, dict):
                    logger.warning(f"session_info is not a dict for task {session['task_id']}: {type(session_info)}")
                    session_info = {'status': None, 'result': None, 'task_info': None}
                
                # Map status
                status_mapping = {
                    'pending': 'waiting',
                    'running': 'processing',
                    'completed': 'completed',
                    'failed': 'error',
                    'cancelled': 'stopped',
                    'retrying': 'processing'
                }
                
                status = status_mapping.get(session.get('status', 'unknown'), 'unknown')
            except Exception as e:
                logger.error(f"Error processing session {session.get('task_id', 'unknown')}: {e}")
                # Create a minimal response for failed sessions
                responses.append(AutomationStatusResponse(
                    status="error",
                    session_id=session.get('task_id', 'unknown'),
                    progress=0,
                    current_step="Error retrieving session info",
                    message=f"Error: {str(e)}"
                ))
                continue
            
            # Calculate progress
            progress = 0
            if session['status'] == 'running':
                progress = 50
            elif session['status'] == 'completed':
                progress = 100
            
            # Get items found/processed
            items_found = 0
            items_processed = 0
            try:
                result_obj = session_info.get('result')
                if result_obj and hasattr(result_obj, 'result') and result_obj.result:
                    if isinstance(result_obj.result, dict):
                        items_found = result_obj.result.get('tenders_found', 0)
                        items_processed = result_obj.result.get('tenders_processed', 0)
            except (AttributeError, TypeError) as e:
                logger.debug(f"Could not extract items count: {e}")
                # Continue with default values
            
            responses.append(AutomationStatusResponse(
                status=status,
                session_id=session.get('task_id', 'unknown'),
                progress=progress,
                current_step=f"{session.get('source', 'unknown')} automation {session.get('status', 'unknown')}",
                items_found=items_found,
                items_processed=items_processed,
                enhanced=True,
                message=f"Session {session.get('task_id', 'unknown')} is {session.get('status', 'unknown')}"
            ))
        
        return responses
        
    except Exception as e:
        logger.error(f"Failed to list sessions: {str(e)}")
        raise AutomationException(f"Failed to list sessions: {str(e)}")


@router.get("/metrics", response_model=SuccessResponse)
async def get_automation_metrics(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get automation system metrics
    """
    try:
        metrics = automation_manager.get_metrics()
        
        return SuccessResponse(
            data={
                "task_metrics": metrics,
                "health_status": {
                    "status": "healthy" if metrics['tasks_failed'] < metrics['tasks_completed'] else "degraded",
                    "active_tasks": metrics['active_tasks'],
                    "pending_tasks": metrics['pending_tasks'],
                    "success_rate": (metrics['tasks_completed'] / max(metrics['tasks_created'], 1)) * 100
                }
            },
            message="Automation metrics retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to get metrics: {str(e)}")
        raise AutomationException(f"Failed to get metrics: {str(e)}")


@router.post("/health-check", response_model=SuccessResponse)
async def automation_health_check(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Check automation system health
    """
    try:
        metrics = automation_manager.get_metrics()
        
        # Health checks
        health_status = {
            'status': 'healthy',
            'task_manager_running': True,
            'active_tasks': metrics['active_tasks'],
            'pending_tasks': metrics['pending_tasks'],
            'failed_tasks_ratio': metrics['tasks_failed'] / max(metrics['tasks_created'], 1),
            'issues': []
        }
        
        # Check for issues
        if metrics['active_tasks'] > 10:
            health_status['issues'].append('High number of active tasks')
        
        if health_status['failed_tasks_ratio'] > 0.5:
            health_status['issues'].append('High failure rate')
            health_status['status'] = 'degraded'
        
        if metrics['retrying_tasks'] > 5:
            health_status['issues'].append('Many tasks retrying')
            health_status['status'] = 'degraded'
        
        return SuccessResponse(
            data=health_status,
            message=f"Automation system is {health_status['status']}"
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise AutomationException(f"Health check failed: {str(e)}")