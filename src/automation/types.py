"""
Automation Module Type Definitions
Clean type definitions for better code readability and IDE support
"""
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from .constants import TaskStatus, TaskPriority, ScraperSource


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

    def is_successful(self) -> bool:
        """Check if task completed successfully"""
        return self.status == TaskStatus.COMPLETED and self.error is None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'task_id': self.task_id,
            'status': self.status.value,
            'result': self.result,
            'error': self.error,
            'execution_time': self.execution_time,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'metadata': self.metadata
        }


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
    created_at: datetime = field(default_factory=lambda: datetime.now())
    last_attempt: Optional[datetime] = None
    next_retry: Optional[datetime] = None
    result: Optional[TaskResult] = None

    def can_retry(self) -> bool:
        """Check if task can be retried"""
        return (
            self.status in [TaskStatus.FAILED, TaskStatus.RETRYING] and
            self.retry_count < self.max_retries
        )

    def is_ready_for_retry(self) -> bool:
        """Check if task is ready for retry"""
        return (
            self.can_retry() and
            self.next_retry is not None and
            datetime.now() >= self.next_retry
        )


@dataclass
class ScrapingSession:
    """Scraping session information"""
    session_id: str
    source: ScraperSource
    user_id: Optional[str] = None
    config: Dict[str, Any] = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    tenders_found: int = 0
    tenders_processed: int = 0
    pages_processed: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now())

    def duration_seconds(self) -> Optional[float]:
        """Calculate session duration in seconds"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    def success_rate(self) -> float:
        """Calculate success rate (processed/found)"""
        if self.tenders_found == 0:
            return 0.0
        return self.tenders_processed / self.tenders_found


@dataclass
class ScrapingResult:
    """Result from a scraping operation"""
    session_id: str
    status: str
    tenders_found: int
    tenders_processed: int
    data: List[Dict[str, Any]]
    errors: List[str]
    start_time: str
    end_time: str
    execution_time: Optional[float] = None
    source: str = ""
    extractor: str = ""
    features_used: Dict[str, bool] = field(default_factory=dict)

    def is_successful(self) -> bool:
        """Check if scraping was successful"""
        return self.status == "completed" and len(self.errors) == 0

    def has_data(self) -> bool:
        """Check if scraping found any data"""
        return len(self.data) > 0


@dataclass
class AutomationMetrics:
    """Automation system metrics"""
    tasks_created: int = 0
    tasks_completed: int = 0
    tasks_failed: int = 0
    tasks_retried: int = 0
    average_execution_time: float = 0.0
    active_tasks: int = 0
    pending_tasks: int = 0
    retrying_tasks: int = 0
    total_tasks: int = 0

    def success_rate(self) -> float:
        """Calculate overall success rate"""
        total = self.tasks_completed + self.tasks_failed
        if total == 0:
            return 0.0
        return self.tasks_completed / total

    def failure_rate(self) -> float:
        """Calculate failure rate"""
        return 1.0 - self.success_rate()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'tasks_created': self.tasks_created,
            'tasks_completed': self.tasks_completed,
            'tasks_failed': self.tasks_failed,
            'tasks_retried': self.tasks_retried,
            'average_execution_time': self.average_execution_time,
            'active_tasks': self.active_tasks,
            'pending_tasks': self.pending_tasks,
            'retrying_tasks': self.retrying_tasks,
            'total_tasks': self.total_tasks,
            'success_rate': self.success_rate(),
            'failure_rate': self.failure_rate()
        }


@dataclass
class HealthStatus:
    """System health status"""
    status: str  # "healthy", "degraded", "unhealthy"
    checks: Dict[str, bool] = field(default_factory=dict)
    metrics: Optional[AutomationMetrics] = None
    issues: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now())

    def is_healthy(self) -> bool:
        """Check if system is healthy"""
        return self.status == "healthy"

    def add_issue(self, issue: str) -> None:
        """Add a health issue"""
        self.issues.append(issue)
        if self.status == "healthy":
            self.status = "degraded"


# Type aliases for better readability
TaskFunction = Callable[..., Any]
TaskId = str
SessionId = str
UserId = str
ConfigDict = Dict[str, Any]
MetadataDict = Dict[str, Any]