# Automation Module

Clean, service-oriented automation system for VisionSeal Complete.

## Architecture

The automation module follows a service-oriented architecture with clear separation of concerns:

```
automation/
├── constants.py         # Centralized configuration values and enums
├── types.py            # Type definitions and data classes
├── manager.py          # Main orchestrator for all automation services
├── services/           # Service implementations
│   ├── task_service.py     # Task creation and execution
│   ├── scraper_service.py  # Scraper loading and configuration
│   ├── session_service.py  # Session management and tracking
│   └── health_service.py   # System health monitoring
├── scrapers/           # Scraper adapters and implementations
└── README.md           # This file
```

## Services Overview

### TaskService (`task_service.py`)
- Creates and manages background tasks
- Handles task execution with ThreadPoolExecutor
- Provides task status tracking and result handling
- Supports retries and error recovery

### ScraperService (`scraper_service.py`)
- Loads and manages available scrapers
- Handles configuration and validation
- Provides graceful fallback from enhanced to basic scrapers
- Manages scraper lifecycle

### SessionService (`session_service.py`)
- Creates and tracks scraping sessions
- Links sessions to background tasks
- Provides session status and metrics
- Handles session cancellation and cleanup

### HealthService (`health_service.py`)
- Monitors system health and performance
- Checks resource usage (CPU, memory)
- Validates task and session metrics
- Generates performance reports and recommendations

## Usage

### Starting a Scraping Session

```python
from automation.manager import automation_manager

# Start scraping for a specific source
session_id = automation_manager.start_scraping(
    source="ungm",
    user_id="user123",
    config={"max_pages": 10},
    priority=TaskPriority.HIGH
)

# Check session status
status = automation_manager.get_session_status(session_id)
```

### Monitoring System Health

```python
# Get health summary
health = automation_manager.get_health_summary()

# Get detailed system status
status = automation_manager.get_system_status()

# Get performance metrics
metrics = automation_manager.get_metrics()
```

### Available Scrapers

```python
# List available scrapers
scrapers = automation_manager.get_available_scrapers()

# Get scraper capabilities
capabilities = automation_manager.get_scraper_capabilities()
```

## Configuration

The automation system uses a hierarchical configuration approach:

1. **Default Values** (`constants.py`) - Baseline configuration
2. **Environment Config** - Environment-specific overrides
3. **Profile Config** - Named configuration profiles
4. **User Config** - Per-request overrides

## Error Handling

The system includes comprehensive error handling:

- **Graceful Degradation**: Falls back to basic scrapers if enhanced unavailable
- **Retry Logic**: Automatic retries with exponential backoff
- **Health Monitoring**: Continuous health checks with alerting
- **Resource Management**: Automatic cleanup of old tasks and sessions

## Performance Features

- **Concurrent Execution**: Multiple scrapers can run simultaneously
- **Resource Monitoring**: CPU and memory usage tracking
- **Performance Analytics**: Detailed metrics and recommendations
- **Background Maintenance**: Automatic cleanup and health checks

## API Integration

The automation system integrates with FastAPI through clean routers:

- `/api/automation/` - Legacy endpoints
- `/api/clean/automation/` - New clean endpoints

The clean router provides simplified, well-documented endpoints using the service architecture.