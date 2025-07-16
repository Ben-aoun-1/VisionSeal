"""
Session Service
Handles scraping session management and tracking
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

from ..constants import TaskStatus, TaskPriority, ScraperSource
from ..types import ScrapingSession, AutomationTask, ConfigDict
from .task_service import TaskService
from .scraper_service import ScraperService
from core.logging.setup import get_logger

logger = get_logger("session_service")


class SessionService:
    """Service for managing scraping sessions"""
    
    def __init__(self, task_service: TaskService, scraper_service: ScraperService):
        self.task_service = task_service
        self.scraper_service = scraper_service
        self.sessions: Dict[str, ScrapingSession] = {}
        self.task_to_session: Dict[str, str] = {}  # Map task_id to session_id
    
    def create_scraping_session(
        self,
        source: str,
        user_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        priority: TaskPriority = TaskPriority.MEDIUM,
        profile: Optional[str] = None
    ) -> Optional[str]:
        """Create a new scraping session"""
        
        # Validate scraper availability
        if not self.scraper_service.is_scraper_available(source):
            logger.error(f"Scraper source '{source}' is not available")
            return None
        
        # Create session
        session_id = f"{source}_{uuid.uuid4().hex[:12]}"
        
        session = ScrapingSession(
            session_id=session_id,
            source=ScraperSource(source),
            user_id=user_id,
            config=config or {},
            status=TaskStatus.PENDING
        )
        
        self.sessions[session_id] = session
        
        # Get scraper function and create task config
        scraper_function = self.scraper_service.get_scraper_function(source)
        task_config = self.scraper_service.create_scraping_task_config(source, config, profile)
        
        # Create background task
        task_id = self.task_service.create_task(
            name=f"Scraping {source.upper()} for session {session_id}",
            function=scraper_function,
            kwargs={'config': task_config},
            priority=priority,
            metadata={
                'session_id': session_id,
                'source': source,
                'user_id': user_id,
                'profile': profile,
                'created_by': 'session_service'
            }
        )
        
        # Link task to session
        self.task_to_session[task_id] = session_id
        session.metadata['task_id'] = task_id
        
        logger.info(f"Created scraping session {session_id} for {source} (task: {task_id})")
        return session_id
    
    def start_session(self, session_id: str) -> bool:
        """Start a scraping session"""
        session = self.sessions.get(session_id)
        if not session:
            logger.error(f"Session {session_id} not found")
            return False
        
        task_id = session.metadata.get('task_id')
        if not task_id:
            logger.error(f"No task associated with session {session_id}")
            return False
        
        # Submit task for execution
        success = self.task_service.submit_task(task_id)
        if success:
            session.status = TaskStatus.RUNNING
            session.start_time = datetime.now()
            logger.info(f"Started scraping session {session_id}")
        else:
            logger.error(f"Failed to start task for session {session_id}")
        
        return success
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get detailed status of a scraping session"""
        session = self.sessions.get(session_id)
        if not session:
            return {'error': f'Session {session_id} not found'}
        
        task_id = session.metadata.get('task_id')
        task_status = None
        task_result = None
        task_info = None
        
        if task_id:
            task_status = self.task_service.get_task_status(task_id)
            task_result = self.task_service.get_task_result(task_id)
            task_info = self.task_service.get_task_info(task_id)
            
            # Update session status based on task status
            if task_status and task_status != session.status:
                session.status = task_status
                
                if task_status == TaskStatus.COMPLETED and task_result:
                    session.end_time = datetime.now()
                    # Extract metrics from task result if available
                    if isinstance(task_result.result, dict):
                        result_data = task_result.result
                        session.tenders_found = result_data.get('tenders_found', 0)
                        session.tenders_processed = result_data.get('tenders_processed', 0)
                        session.pages_processed = result_data.get('pages_processed', 0)
                
                elif task_status == TaskStatus.FAILED and task_result:
                    session.end_time = datetime.now()
                    session.error_message = task_result.error
        
        return {
            'session_id': session_id,
            'status': session.status.value if session.status else None,
            'source': session.source.value,
            'user_id': session.user_id,
            'tenders_found': session.tenders_found,
            'tenders_processed': session.tenders_processed,
            'pages_processed': session.pages_processed,
            'start_time': session.start_time.isoformat() if session.start_time else None,
            'end_time': session.end_time.isoformat() if session.end_time else None,
            'duration_seconds': session.duration_seconds(),
            'success_rate': session.success_rate(),
            'error_message': session.error_message,
            'task_id': task_id,
            'task_status': task_status.value if task_status else None,
            'task_result': task_result.to_dict() if task_result else None,
            'task_info': task_info,
            'created_at': session.created_at.isoformat(),
            'config': session.config,
            'metadata': session.metadata
        }
    
    def cancel_session(self, session_id: str) -> bool:
        """Cancel a scraping session"""
        session = self.sessions.get(session_id)
        if not session:
            logger.error(f"Session {session_id} not found")
            return False
        
        task_id = session.metadata.get('task_id')
        if task_id:
            success = self.task_service.cancel_task(task_id)
            if success:
                session.status = TaskStatus.CANCELLED
                session.end_time = datetime.now()
                logger.info(f"Cancelled scraping session {session_id}")
                return True
        
        return False
    
    def list_sessions(
        self, 
        user_id: Optional[str] = None,
        source: Optional[str] = None,
        status: Optional[TaskStatus] = None
    ) -> List[Dict[str, Any]]:
        """List scraping sessions with optional filters"""
        sessions = []
        
        for session_id, session in self.sessions.items():
            # Apply filters
            if user_id and session.user_id != user_id:
                continue
            if source and session.source.value != source:
                continue
            if status and session.status != status:
                continue
            
            # Get basic session info
            session_info = {
                'session_id': session_id,
                'source': session.source.value,
                'status': session.status.value,
                'user_id': session.user_id,
                'tenders_found': session.tenders_found,
                'tenders_processed': session.tenders_processed,
                'start_time': session.start_time.isoformat() if session.start_time else None,
                'end_time': session.end_time.isoformat() if session.end_time else None,
                'duration_seconds': session.duration_seconds(),
                'created_at': session.created_at.isoformat(),
                'task_id': session.metadata.get('task_id')
            }
            
            sessions.append(session_info)
        
        # Sort by creation time (newest first)
        sessions.sort(key=lambda s: s['created_at'], reverse=True)
        return sessions
    
    def get_session_metrics(self) -> Dict[str, Any]:
        """Get session-related metrics"""
        total_sessions = len(self.sessions)
        
        status_counts = {}
        source_counts = {}
        total_tenders_found = 0
        total_tenders_processed = 0
        
        for session in self.sessions.values():
            # Count by status
            status = session.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # Count by source
            source = session.source.value
            source_counts[source] = source_counts.get(source, 0) + 1
            
            # Sum tender counts
            total_tenders_found += session.tenders_found
            total_tenders_processed += session.tenders_processed
        
        return {
            'total_sessions': total_sessions,
            'status_breakdown': status_counts,
            'source_breakdown': source_counts,
            'total_tenders_found': total_tenders_found,
            'total_tenders_processed': total_tenders_processed,
            'overall_success_rate': (
                total_tenders_processed / total_tenders_found 
                if total_tenders_found > 0 else 0.0
            )
        }
    
    def cleanup_old_sessions(self, hours_old: int = 72) -> int:
        """Clean up old completed sessions"""
        from datetime import timedelta
        
        cutoff_time = datetime.now() - timedelta(hours=hours_old)
        sessions_to_remove = []
        
        for session_id, session in self.sessions.items():
            if (session.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED] and
                session.end_time and session.end_time < cutoff_time):
                sessions_to_remove.append(session_id)
        
        # Remove old sessions
        for session_id in sessions_to_remove:
            session = self.sessions.pop(session_id, None)
            if session and session.metadata.get('task_id'):
                # Also remove from task-to-session mapping
                task_id = session.metadata['task_id']
                self.task_to_session.pop(task_id, None)
        
        logger.info(f"Cleaned up {len(sessions_to_remove)} old sessions")
        return len(sessions_to_remove)