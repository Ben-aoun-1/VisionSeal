"""
Automation Module Constants
Centralized configuration values and constants for the automation system
"""
from enum import Enum
from typing import Dict, Any


class TaskStatus(str, Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class TaskPriority(str, Enum):
    """Task priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class ScraperSource(str, Enum):
    """Available scraper sources"""
    UNGM = "ungm"
    TUNIPAGES = "tunipages"


class AutomationDefaults:
    """Default configuration values for automation"""
    
    # Task Management
    MAX_WORKERS = 4
    MAX_RETRIES = 3
    RETRY_DELAY = 300  # 5 minutes
    TASK_TIMEOUT = 3600  # 1 hour
    SCHEDULER_INTERVAL = 30  # 30 seconds
    
    # Scraper Settings
    MAX_PAGES = 10
    REQUEST_DELAY = 2  # seconds
    BROWSER_TIMEOUT = 30000  # milliseconds
    HEADLESS = True
    
    # Performance
    MAX_CONCURRENT_SCRAPERS = 2
    MEMORY_THRESHOLD_MB = 1024
    CPU_THRESHOLD_PERCENT = 80
    
    # Cleanup
    CLEANUP_HOURS = 24
    CLEANUP_FAILED_HOURS = 72
    
    # Monitoring
    METRICS_RETENTION_DAYS = 30
    ALERT_FAILURE_THRESHOLD = 0.5
    HEALTH_CHECK_INTERVAL = 60


class ErrorCodes:
    """Standard error codes for automation"""
    
    # Task Errors
    TASK_NOT_FOUND = "TASK_NOT_FOUND"
    TASK_ALREADY_RUNNING = "TASK_ALREADY_RUNNING"
    TASK_CREATION_FAILED = "TASK_CREATION_FAILED"
    TASK_EXECUTION_FAILED = "TASK_EXECUTION_FAILED"
    
    # Scraper Errors
    SCRAPER_NOT_AVAILABLE = "SCRAPER_NOT_AVAILABLE"
    SCRAPER_INITIALIZATION_FAILED = "SCRAPER_INITIALIZATION_FAILED"
    SCRAPER_EXECUTION_FAILED = "SCRAPER_EXECUTION_FAILED"
    
    # Configuration Errors
    INVALID_CONFIG = "INVALID_CONFIG"
    MISSING_CREDENTIALS = "MISSING_CREDENTIALS"
    
    # System Errors
    INSUFFICIENT_RESOURCES = "INSUFFICIENT_RESOURCES"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"


class AutomationMessages:
    """Standard messages for automation operations"""
    
    # Success Messages
    TASK_CREATED = "Task created successfully"
    TASK_STARTED = "Task started successfully"
    TASK_COMPLETED = "Task completed successfully"
    SCRAPER_LOADED = "Scraper loaded successfully"
    
    # Error Messages
    TASK_FAILED = "Task execution failed"
    SCRAPER_UNAVAILABLE = "Scraper is not available"
    INVALID_PARAMETERS = "Invalid parameters provided"
    SYSTEM_OVERLOADED = "System is currently overloaded"
    
    # Info Messages
    FALLBACK_ACTIVATED = "Fallback scraper activated"
    RETRY_SCHEDULED = "Task retry scheduled"
    CLEANUP_STARTED = "Cleanup process started"


class ScraperConfig:
    """Configuration templates for different scrapers"""
    
    UNGM_CONFIG = {
        "max_pages": AutomationDefaults.MAX_PAGES,
        "timeout": AutomationDefaults.BROWSER_TIMEOUT,
        "headless": AutomationDefaults.HEADLESS,
        "countries": [
            "Tunisia", "Morocco", "Algeria", "Egypt", "Libya", "Sudan",
            "Nigeria", "Ghana", "Senegal", "Mali", "Burkina Faso", "Niger",
            "Kenya", "Ethiopia", "Tanzania", "Uganda", "Rwanda"
        ],
        "keywords": [
            "consulting", "conseil", "advisory", "technical assistance",
            "capacity building", "training", "formation", "étude"
        ]
    }
    
    TUNIPAGES_CONFIG = {
        "max_pages": AutomationDefaults.MAX_PAGES,
        "timeout": AutomationDefaults.BROWSER_TIMEOUT,
        "headless": AutomationDefaults.HEADLESS,
        "enable_authentication": True,
        "enable_document_processing": True,
        "countries": [
            "TUNISIE", "MAROC", "BENIN", "BURKINA FASO", "CAMEROUN",
            "TCHAD", "ALGERIE", "SENEGAL", "TOGO", "NIGER"
        ],
        "keywords": [
            "formation", "emploi", "entrepreneuriat", "consulting",
            "conseil", "management", "étude", "expertise", "audit"
        ]
    }


class HealthCheckThresholds:
    """Thresholds for system health monitoring"""
    
    MAX_ACTIVE_TASKS = 10
    MAX_FAILED_RATIO = 0.8  # More tolerant of failures during startup
    MAX_RETRY_TASKS = 5
    MIN_SUCCESS_RATE = 0.3  # Lower threshold for new systems
    MAX_MEMORY_USAGE_MB = 2048
    MAX_CPU_USAGE_PERCENT = 90
    MIN_TASKS_FOR_RATE_CHECK = 5  # Only check rates if we have enough data