"""
Task Service
Handles task creation, execution, and management
"""
import uuid
import time
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, Future

from ..constants import TaskStatus, TaskPriority, AutomationDefaults, ErrorCodes
from ..types import AutomationTask, TaskResult, AutomationMetrics
from core.logging.setup import get_logger

logger = get_logger("task_service")


class TaskService:
    """Service for managing automation tasks"""
    
    def __init__(self, max_workers: Optional[int] = None):
        self.max_workers = max_workers or AutomationDefaults.MAX_WORKERS
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        
        # Task storage
        self.tasks: Dict[str, AutomationTask] = {}
        self.running_tasks: Dict[str, Future] = {}
        
        # Metrics
        self.metrics = AutomationMetrics()
        
        logger.info(f"Task Service initialized with {self.max_workers} workers")
    
    def create_task(
        self,
        name: str,
        function: Callable,
        args: tuple = (),
        kwargs: Optional[Dict[str, Any]] = None,
        priority: TaskPriority = TaskPriority.MEDIUM,
        max_retries: int = AutomationDefaults.MAX_RETRIES,
        retry_delay: int = AutomationDefaults.RETRY_DELAY,
        timeout: Optional[int] = None,
        dependencies: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
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
            dependencies=dependencies or [],
            metadata=metadata or {}
        )
        
        self.tasks[task_id] = task
        self.metrics.tasks_created += 1
        
        logger.info(f"Created task {task_id}: {name}")
        return task_id
    
    def submit_task(self, task_id: str) -> bool:
        """Submit task for execution"""
        if not self._validate_task_for_submission(task_id):
            return False
        
        task = self.tasks[task_id]
        
        # Submit to executor
        future = self.executor.submit(self._execute_task, task)
        self.running_tasks[task_id] = future
        task.status = TaskStatus.RUNNING
        task.last_attempt = datetime.now()
        
        logger.info(f"Submitted task {task_id} for execution")
        return True
    
    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get current status of a task"""
        task = self.tasks.get(task_id)
        return task.status if task else None
    
    def get_task_result(self, task_id: str) -> Optional[TaskResult]:
        """Get result of a completed task"""
        task = self.tasks.get(task_id)
        return task.result if task else None
    
    def get_task_info(self, task_id: str) -> Optional[AutomationTask]:
        """Get full task information"""
        return self.tasks.get(task_id)
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending or running task"""
        if task_id not in self.tasks:
            logger.warning(f"Task {task_id} not found for cancellation")
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
    
    def list_tasks(self, status_filter: Optional[TaskStatus] = None) -> List[AutomationTask]:
        """List tasks with optional status filter"""
        tasks = list(self.tasks.values())
        
        if status_filter:
            tasks = [task for task in tasks if task.status == status_filter]
        
        # Sort by creation date (newest first)
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        return tasks
    
    def get_metrics(self) -> AutomationMetrics:
        """Get current metrics"""
        # Update real-time metrics
        self.metrics.active_tasks = len([t for t in self.tasks.values() if t.status == TaskStatus.RUNNING])
        self.metrics.pending_tasks = len([t for t in self.tasks.values() if t.status == TaskStatus.PENDING])
        self.metrics.retrying_tasks = len([t for t in self.tasks.values() if t.status == TaskStatus.RETRYING])
        self.metrics.total_tasks = len(self.tasks)
        
        return self.metrics
    
    def cleanup_completed_tasks(self, hours_old: int = AutomationDefaults.CLEANUP_HOURS) -> int:
        """Clean up old completed tasks"""
        cutoff_time = datetime.now() - timedelta(hours=hours_old)
        
        tasks_to_remove = []
        for task_id, task in self.tasks.items():
            if (task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED] and
                task.result and 
                task.result.completed_at and
                task.result.completed_at < cutoff_time):
                tasks_to_remove.append(task_id)
        
        for task_id in tasks_to_remove:
            del self.tasks[task_id]
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]
        
        logger.info(f"Cleaned up {len(tasks_to_remove)} old tasks")
        return len(tasks_to_remove)
    
    def shutdown(self) -> None:
        """Shutdown the task service"""
        logger.info("Shutting down task service...")
        
        # Cancel all pending tasks
        for task_id, task in self.tasks.items():
            if task.status == TaskStatus.PENDING:
                self.cancel_task(task_id)
        
        # Wait for running tasks to complete
        self.executor.shutdown(wait=True)
        
        logger.info("Task service shutdown complete")
    
    def _validate_task_for_submission(self, task_id: str) -> bool:
        """Validate task can be submitted"""
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
        
        return True
    
    def _check_dependencies(self, task: AutomationTask) -> bool:
        """Check if task dependencies are satisfied"""
        for dep_id in task.dependencies:
            if dep_id not in self.tasks:
                return False
            
            dep_task = self.tasks[dep_id]
            if dep_task.status != TaskStatus.COMPLETED:
                return False
        
        return True
    
    def _execute_task(self, task: AutomationTask) -> TaskResult:
        """Execute a single task"""
        start_time = time.time()
        started_at = datetime.now()
        
        logger.info(f"Executing task {task.id}: {task.name}")
        
        try:
            # Execute the task function
            result = task.function(*task.args, **task.kwargs)
            
            execution_time = time.time() - start_time
            completed_at = datetime.now()
            
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
            self.metrics.tasks_completed += 1
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
                completed_at=datetime.now(),
                metadata=task.metadata
            )
            
            task.status = TaskStatus.FAILED
            task.result = task_result
            
            # Schedule retry if applicable
            if task.can_retry():
                task.retry_count += 1
                task.next_retry = datetime.now() + timedelta(seconds=task.retry_delay)
                task.status = TaskStatus.RETRYING
                self.metrics.tasks_retried += 1
                
                logger.warning(f"Task {task.id} failed, scheduling retry {task.retry_count}/{task.max_retries}")
            else:
                self.metrics.tasks_failed += 1
                logger.error(f"Task {task.id} failed permanently: {error_msg}")
            
            return task_result
        
        finally:
            # Remove from running tasks
            if task.id in self.running_tasks:
                del self.running_tasks[task.id]
    
    def _update_average_execution_time(self, execution_time: float) -> None:
        """Update average execution time metric"""
        total_completed = self.metrics.tasks_completed
        current_avg = self.metrics.average_execution_time
        
        # Calculate new average
        if total_completed == 1:
            new_avg = execution_time
        else:
            new_avg = ((current_avg * (total_completed - 1)) + execution_time) / total_completed
        
        self.metrics.average_execution_time = new_avg