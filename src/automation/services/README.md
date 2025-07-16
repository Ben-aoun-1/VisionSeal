# Automation Services

This directory contains the core service implementations for the automation system.

## Service Descriptions

### TaskService
**Purpose**: Background task management and execution  
**File**: `task_service.py`

- Creates and queues background tasks
- Manages ThreadPoolExecutor for concurrent execution
- Tracks task status, results, and metrics
- Handles retries and error recovery
- Provides task cancellation and cleanup

**Key Methods**:
- `create_task()` - Create a new background task
- `submit_task()` - Submit task for execution
- `get_task_status()` - Get current task status
- `cancel_task()` - Cancel a running task
- `get_metrics()` - Get task execution metrics

### ScraperService
**Purpose**: Scraper loading, configuration, and coordination  
**File**: `scraper_service.py`

- Dynamically loads available scrapers
- Manages scraper configurations and profiles
- Provides graceful fallback from enhanced to basic scrapers
- Validates scraper configurations
- Creates complete task configurations

**Key Methods**:
- `get_available_scrapers()` - List available scraper sources
- `get_scraper_function()` - Get scraper function for execution
- `get_scraper_config()` - Get merged configuration
- `create_scraping_task_config()` - Create complete task config

### SessionService
**Purpose**: Scraping session management and tracking  
**File**: `session_service.py`

- Creates and manages scraping sessions
- Links sessions to background tasks
- Tracks session progress and results
- Provides session metrics and analytics
- Handles session cancellation and cleanup

**Key Methods**:
- `create_scraping_session()` - Create new session
- `start_session()` - Start session execution
- `get_session_status()` - Get detailed session status
- `cancel_session()` - Cancel running session
- `list_sessions()` - List sessions with filters

### HealthService
**Purpose**: System health monitoring and performance analysis  
**File**: `health_service.py`

- Monitors automation system health
- Checks resource usage (CPU, memory)
- Validates performance metrics
- Generates health reports
- Provides performance recommendations

**Key Methods**:
- `check_system_health()` - Comprehensive health check
- `get_health_summary()` - Health status summary
- `get_system_status()` - Detailed system status
- `get_performance_report()` - Performance analysis

## Service Dependencies

```
AutomationManager
├── TaskService (independent)
├── ScraperService (independent)
├── SessionService (depends on TaskService, ScraperService)
└── HealthService (depends on TaskService, SessionService)
```

## Error Handling Patterns

All services follow consistent error handling:

1. **Logging**: Structured logging with appropriate levels
2. **Graceful Degradation**: Fallback options when possible
3. **Exception Propagation**: Clean exception handling up the stack
4. **Resource Cleanup**: Proper cleanup in finally blocks

## Performance Considerations

- **Async Operations**: Where applicable, async/await patterns
- **Resource Pooling**: Efficient use of thread pools
- **Caching**: Configuration and scraper function caching
- **Cleanup**: Regular cleanup of completed tasks and sessions

## Configuration

Services use configuration from:
- Environment variables
- Configuration files
- Runtime overrides
- Default constants

See `../constants.py` for default values and configuration options.