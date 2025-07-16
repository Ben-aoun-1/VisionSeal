"""
Background Task Manager for VisionSeal Automation
Handles scheduling, execution, and monitoring of automation tasks
"""
import asyncio
import threading
import time
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Callable, Union
from enum import Enum
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, Future
import json

from core.config.settings import settings
from core.config.manager import config_manager
from core.logging.setup import get_logger
from core.database.connection import db_manager
from core.database.repositories import AutomationSessionRepository
from models.tender import TenderSource

logger = get_logger("task_manager")


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


@dataclass
class TaskResult:
    """Result of task execution"""
    task_id: str
    status: TaskStatus
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AutomationTask:
    """Automation task definition"""
    id: str
    name: str
    function: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.MEDIUM
    max_retries: int = 3
    retry_delay: int = 60  # seconds
    timeout: Optional[int] = None  # seconds
    schedule: Optional[Dict[str, Any]] = None  # For recurring tasks
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Runtime state
    status: TaskStatus = TaskStatus.PENDING
    retry_count: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_attempt: Optional[datetime] = None
    next_retry: Optional[datetime] = None
    result: Optional[TaskResult] = None


class TaskManager:
    """Background task manager for automation workflows"""
    
    def __init__(self, max_workers: int = None):
        # Get configuration from config manager
        automation_config = config_manager.get_automation_config()
        task_manager_config = automation_config.get('task_manager', {})
        
        self.max_workers = (
            max_workers or 
            task_manager_config.get('max_workers') or 
            settings.automation.max_workers or 
            4
        )
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        
        # Task storage
        self.tasks: Dict[str, AutomationTask] = {}
        self.running_tasks: Dict[str, Future] = {}
        self.completed_tasks: Dict[str, TaskResult] = {}
        
        # Scheduling
        self.scheduler_running = False
        self.scheduler_thread: Optional[threading.Thread] = None
        
        # Metrics
        self.metrics = {
            'tasks_created': 0,
            'tasks_completed': 0,
            'tasks_failed': 0,
            'tasks_retried': 0,
            'average_execution_time': 0.0
        }
        
        logger.info(f"Task Manager initialized with {self.max_workers} workers")
    
    def create_task(
        self,
        name: str,
        function: Callable,
        args: tuple = (),
        kwargs: Dict[str, Any] = None,
        priority: TaskPriority = TaskPriority.MEDIUM,
        max_retries: int = 3,
        retry_delay: int = 60,
        timeout: Optional[int] = None,
        schedule: Optional[Dict[str, Any]] = None,
        dependencies: List[str] = None,
        metadata: Dict[str, Any] = None
    ) -> str:
        """Create a new automation task"""
        task_id = f"task_{uuid.uuid4().hex[:12]}"
        
        task = AutomationTask(
            id=task_id,
            name=name,
            function=function,
            args=args,
            kwargs=kwargs or {},
            priority=priority,
            max_retries=max_retries,
            retry_delay=retry_delay,
            timeout=timeout,
            schedule=schedule,
            dependencies=dependencies or [],
            metadata=metadata or {}
        )
        
        self.tasks[task_id] = task
        self.metrics['tasks_created'] += 1
        
        logger.info(f"Created task {task_id}: {name}")
        return task_id
    
    def submit_task(self, task_id: str) -> bool:
        """Submit task for execution"""
        if task_id not in self.tasks:
            logger.error(f"Task {task_id} not found")
            return False
        
        task = self.tasks[task_id]
        
        # Check dependencies
        if not self._check_dependencies(task):
            logger.warning(f"Task {task_id} dependencies not satisfied")
            return False
        
        # Check if already running
        if task_id in self.running_tasks:
            logger.warning(f"Task {task_id} is already running")
            return False
        
        # Submit to executor
        future = self.executor.submit(self._execute_task, task)
        self.running_tasks[task_id] = future
        task.status = TaskStatus.RUNNING
        task.last_attempt = datetime.now(timezone.utc)
        
        logger.info(f"Submitted task {task_id} for execution")
        return True
    
    def _execute_task(self, task: AutomationTask) -> TaskResult:
        """Execute a single task"""
        start_time = time.time()
        started_at = datetime.now(timezone.utc)
        
        logger.info(f"Executing task {task.id}: {task.name}")
        
        try:
            # Execute the task function
            if task.timeout:
                # TODO: Implement timeout handling
                result = task.function(*task.args, **task.kwargs)
            else:
                result = task.function(*task.args, **task.kwargs)
            
            execution_time = time.time() - start_time
            completed_at = datetime.now(timezone.utc)
            
            task_result = TaskResult(
                task_id=task.id,
                status=TaskStatus.COMPLETED,
                result=result,
                execution_time=execution_time,
                started_at=started_at,
                completed_at=completed_at,
                metadata=task.metadata
            )
            
            task.status = TaskStatus.COMPLETED
            task.result = task_result
            
            # Update metrics
            self.metrics['tasks_completed'] += 1
            self._update_average_execution_time(execution_time)
            
            logger.info(f"Task {task.id} completed successfully in {execution_time:.2f}s")
            return task_result
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)
            
            task_result = TaskResult(
                task_id=task.id,
                status=TaskStatus.FAILED,
                error=error_msg,
                execution_time=execution_time,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
                metadata=task.metadata
            )
            
            task.status = TaskStatus.FAILED
            task.result = task_result
            
            # Schedule retry if applicable
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.next_retry = datetime.now(timezone.utc) + timedelta(seconds=task.retry_delay)
                task.status = TaskStatus.RETRYING
                self.metrics['tasks_retried'] += 1
                
                logger.warning(f"Task {task.id} failed, scheduling retry {task.retry_count}/{task.max_retries}")
            else:
                self.metrics['tasks_failed'] += 1
                logger.error(f"Task {task.id} failed permanently: {error_msg}")
            
            return task_result
        
        finally:
            # Remove from running tasks
            if task.id in self.running_tasks:
                del self.running_tasks[task.id]
    
    def _check_dependencies(self, task: AutomationTask) -> bool:
        """Check if task dependencies are satisfied"""
        for dep_id in task.dependencies:
            if dep_id not in self.tasks:
                return False
            
            dep_task = self.tasks[dep_id]
            if dep_task.status != TaskStatus.COMPLETED:
                return False
        
        return True
    
    def _update_average_execution_time(self, execution_time: float):
        """Update average execution time metric"""
        total_completed = self.metrics['tasks_completed']
        current_avg = self.metrics['average_execution_time']
        
        # Calculate new average
        new_avg = ((current_avg * (total_completed - 1)) + execution_time) / total_completed
        self.metrics['average_execution_time'] = new_avg
    
    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get current status of a task"""
        if task_id in self.tasks:
            return self.tasks[task_id].status
        return None
    
    def get_task_result(self, task_id: str) -> Optional[TaskResult]:
        """Get result of a completed task"""
        if task_id in self.tasks:
            return self.tasks[task_id].result
        return None
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending or running task"""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        
        # Cancel if running
        if task_id in self.running_tasks:
            future = self.running_tasks[task_id]
            if future.cancel():
                task.status = TaskStatus.CANCELLED
                del self.running_tasks[task_id]
                logger.info(f"Cancelled running task {task_id}")
                return True
        
        # Cancel if pending
        if task.status == TaskStatus.PENDING:
            task.status = TaskStatus.CANCELLED
            logger.info(f"Cancelled pending task {task_id}")
            return True
        
        return False
    
    def start_scheduler(self):
        """Start the background scheduler"""
        if self.scheduler_running:
            return
        
        self.scheduler_running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        logger.info("Task scheduler started")
    
    def stop_scheduler(self):
        """Stop the background scheduler"""
        self.scheduler_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        logger.info("Task scheduler stopped")
    
    def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.scheduler_running:
            try:
                # Process retry queue
                self._process_retries()
                
                # Process scheduled tasks
                self._process_scheduled_tasks()
                
                # Clean up completed tasks
                self._cleanup_old_tasks()
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Scheduler error: {str(e)}")
                time.sleep(60)  # Wait longer on error
    
    def _process_retries(self):
        """Process tasks ready for retry"""
        now = datetime.now(timezone.utc)
        
        for task_id, task in self.tasks.items():
            if (task.status == TaskStatus.RETRYING and 
                task.next_retry and 
                now >= task.next_retry):
                
                logger.info(f"Retrying task {task_id} (attempt {task.retry_count})")
                task.status = TaskStatus.PENDING
                task.next_retry = None
                self.submit_task(task_id)
    
    def _process_scheduled_tasks(self):
        """Process recurring scheduled tasks"""
        # TODO: Implement recurring task scheduling
        pass
    
    def _cleanup_old_tasks(self):
        """Clean up old completed tasks"""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        
        to_remove = []
        for task_id, task in self.tasks.items():
            if (task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED] and
                task.result and 
                task.result.completed_at and
                task.result.completed_at < cutoff):
                to_remove.append(task_id)
        
        for task_id in to_remove:
            del self.tasks[task_id]
            if task_id in self.completed_tasks:
                del self.completed_tasks[task_id]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get task manager metrics"""
        return {
            **self.metrics,
            'active_tasks': len([t for t in self.tasks.values() if t.status == TaskStatus.RUNNING]),
            'pending_tasks': len([t for t in self.tasks.values() if t.status == TaskStatus.PENDING]),
            'retrying_tasks': len([t for t in self.tasks.values() if t.status == TaskStatus.RETRYING]),
            'total_tasks': len(self.tasks)
        }
    
    def shutdown(self):
        """Shutdown task manager"""
        logger.info("Shutting down task manager...")
        
        # Stop scheduler
        self.stop_scheduler()
        
        # Cancel all pending tasks
        for task_id, task in self.tasks.items():
            if task.status == TaskStatus.PENDING:
                self.cancel_task(task_id)
        
        # Wait for running tasks to complete
        self.executor.shutdown(wait=True)
        
        logger.info("Task manager shutdown complete")


class AutomationTaskManager:
    """High-level automation task manager for Topaza.net"""
    
    def __init__(self):
        self.task_manager = TaskManager()
        self.task_manager.start_scheduler()
        
        # Import scrapers dynamically to avoid circular imports
        self._scrapers = {}
        self._load_scrapers()
        
        logger.info("Automation Task Manager initialized")
    
    def _load_scrapers(self):
        """Load available scrapers with enhanced capabilities"""
        self._scrapers = {}
        
        # Try to load production scrapers first
        try:
            from automation.scrapers.ungm_playwright_scraper import run_ungm_scraping
            from automation.scrapers.tunipages_scraper import run_tunipages_scraping
            
            self._scrapers = {
                'ungm': run_ungm_scraping,  # UNGM Playwright scraper
                'tunipages': run_tunipages_scraping  # TuniPages scraper with auth + documents
            }
            
            logger.info(f"✅ Loaded {len(self._scrapers)} PRODUCTION scrapers (Playwright + Document Processing)")
            
        except ImportError as e:
            logger.warning(f"Production scrapers not available: {str(e)}, trying individual imports")
            
            # Fallback to individual loading
            try:
                self._scrapers = {}
                
                try:
                    from automation.scrapers.ungm_playwright_scraper import run_ungm_scraping_sync
                    self._scrapers['ungm'] = run_ungm_scraping_sync
                    logger.info("✅ Loaded UNGM scraper individually (sync wrapper)")
                except ImportError:
                    logger.warning("❌ Could not load UNGM scraper")
                
                try:
                    from automation.scrapers.tunipages_scraper import run_tunipages_scraping_sync
                    self._scrapers['tunipages'] = run_tunipages_scraping_sync
                    logger.info("✅ Loaded TuniPages scraper individually (sync wrapper)")
                except ImportError:
                    logger.warning("❌ Could not load TuniPages scraper")
                
                logger.info(f"⚠️ Loaded {len(self._scrapers)} scrapers individually")
                
            except ImportError as e2:
                logger.error(f"Could not load any scrapers: {str(e2)}")
                # Last resort - try to load individual scrapers
                self._load_individual_scrapers()
    
    def _load_individual_scrapers(self):
        """Load individual scrapers as last resort"""
        # Try production scrapers individually (using sync wrappers)
        try:
            from automation.scrapers.ungm_playwright_scraper import run_ungm_scraping_sync
            self._scrapers['ungm'] = run_ungm_scraping_sync
            logger.info("✅ Loaded UNGM scraper individually (sync wrapper)")
        except ImportError:
            logger.warning("❌ Could not load UNGM scraper")
        
        try:
            from automation.scrapers.tunipages_scraper import run_tunipages_scraping_sync
            self._scrapers['tunipages'] = run_tunipages_scraping_sync
            logger.info("✅ Loaded TuniPages scraper individually (sync wrapper)")
        except ImportError:
            logger.warning("❌ Could not load TuniPages scraper")
    
    def schedule_scraping_session(
        self,
        source: str,
        config: Optional[Dict[str, Any]] = None,
        priority: TaskPriority = TaskPriority.MEDIUM,
        profile: Optional[str] = None
    ) -> Optional[str]:
        """Schedule a scraping session"""
        if source not in self._scrapers:
            logger.error(f"Unknown scraper source: {source}")
            return None

        # Get merged configuration
        merged_config = config_manager.get_merged_config(
            scraper=source,
            profile=profile,
            overrides=config
        )
        
        scraper_function = self._scrapers[source]
        task_name = f"Scraping {source.upper()} for Topaza.net"
        
        # Debug logging
        logger.info(f"🔍 Using scraper function: {scraper_function.__name__} for source: {source}")
        logger.info(f"🔍 Available scrapers: {list(self._scrapers.keys())}")
        
        # Get task settings from config
        automation_config = config_manager.get_automation_config()
        task_config = automation_config.get('task_manager', {})
        
        task_id = self.task_manager.create_task(
            name=task_name,
            function=scraper_function,
            kwargs={'config': merged_config},
            priority=priority,
            max_retries=task_config.get('max_retry_attempts', 2),
            retry_delay=task_config.get('retry_delay', 300),
            timeout=task_config.get('task_timeout', 3600),
            metadata={
                'source': source,
                'config': merged_config,
                'profile': profile,
                'scheduled_by': 'automation_manager'
            }
        )
        
        # Submit immediately
        if self.task_manager.submit_task(task_id):
            logger.info(f"Scheduled {source} scraping session: {task_id}")
            return task_id
        
        return None
    
    def schedule_all_scrapers(
        self,
        config: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Schedule all available scrapers"""
        task_ids = []
        
        for source in self._scrapers.keys():
            task_id = self.schedule_scraping_session(
                source=source,
                config=config,
                priority=TaskPriority.HIGH
            )
            if task_id:
                task_ids.append(task_id)
        
        logger.info(f"Scheduled {len(task_ids)} scraping sessions")
        return task_ids
    
    def get_session_status(self, task_id: str) -> Dict[str, Any]:
        """Get detailed status of scraping session"""
        status = self.task_manager.get_task_status(task_id)
        result = self.task_manager.get_task_result(task_id)
        
        return {
            'task_id': task_id,
            'status': status.value if status else None,
            'result': result,
            'task_info': self.task_manager.tasks.get(task_id)
        }
    
    def get_all_sessions(self) -> List[Dict[str, Any]]:
        """Get status of all sessions"""
        sessions = []
        
        for task_id, task in self.task_manager.tasks.items():
            if task.metadata.get('scheduled_by') == 'automation_manager':
                sessions.append({
                    'task_id': task_id,
                    'name': task.name,
                    'status': task.status.value,
                    'source': task.metadata.get('source'),
                    'created_at': task.created_at,
                    'last_attempt': task.last_attempt,
                    'retry_count': task.retry_count
                })
        
        return sessions
    
    def cancel_session(self, task_id: str) -> bool:
        """Cancel a scraping session"""
        return self.task_manager.cancel_task(task_id)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get automation metrics"""
        return self.task_manager.get_metrics()
    
    def shutdown(self):
        """Shutdown automation task manager"""
        self.task_manager.shutdown()


# Global task manager instance
automation_manager = AutomationTaskManager()