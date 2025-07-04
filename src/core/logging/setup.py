"""
Structured logging setup
Replaces basic file logging from original codebase
"""
import logging
import logging.config
import sys
from pathlib import Path
from typing import Dict, Any
import json
from datetime import datetime

from core.config.settings import settings


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add extra fields
        if hasattr(record, '__dict__'):
            for key, value in record.__dict__.items():
                if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 
                              'pathname', 'filename', 'module', 'lineno', 
                              'funcName', 'created', 'msecs', 'relativeCreated',
                              'thread', 'threadName', 'processName', 'process',
                              'message', 'exc_info', 'exc_text', 'stack_info']:
                    log_entry[key] = value
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, default=str)


class CorrelationFilter(logging.Filter):
    """Add correlation ID to log records"""
    
    def filter(self, record: logging.LogRecord) -> bool:
        # Add correlation ID if not present
        if not hasattr(record, 'correlation_id'):
            record.correlation_id = getattr(self, '_correlation_id', 'unknown')
        return True
    
    def set_correlation_id(self, correlation_id: str):
        """Set correlation ID for current request"""
        self._correlation_id = correlation_id


def get_logging_config() -> Dict[str, Any]:
    """Get logging configuration"""
    
    # Ensure logs directory exists
    settings.logs_dir.mkdir(parents=True, exist_ok=True)
    
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
            },
            "json": {
                "()": JSONFormatter
            }
        },
        "filters": {
            "correlation": {
                "()": CorrelationFilter
            }
        },
        "handlers": {
            "console": {
                "level": "INFO",
                "class": "logging.StreamHandler",
                "formatter": "standard",
                "stream": sys.stdout,
                "filters": ["correlation"]
            },
            "file": {
                "level": "DEBUG",
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "json",
                "filename": str(settings.logs_dir / "visionseal.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "filters": ["correlation"]
            },
            "error_file": {
                "level": "ERROR",
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "json",
                "filename": str(settings.logs_dir / "error.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "filters": ["correlation"]
            }
        },
        "loggers": {
            "visionseal": {
                "level": "DEBUG",
                "handlers": ["console", "file", "error_file"],
                "propagate": False
            },
            "visionseal.automation": {
                "level": "DEBUG",
                "handlers": ["console", "file"],
                "propagate": False
            },
            "visionseal.ai": {
                "level": "DEBUG", 
                "handlers": ["console", "file"],
                "propagate": False
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False
            },
            "sqlalchemy": {
                "level": "WARNING",
                "handlers": ["file"],
                "propagate": False
            }
        },
        "root": {
            "level": "INFO",
            "handlers": ["console", "file"]
        }
    }
    
    # Adjust log levels based on environment
    if settings.environment == "development":
        config["handlers"]["console"]["level"] = "DEBUG"
        config["loggers"]["visionseal"]["level"] = "DEBUG"
    elif settings.environment == "production":
        config["handlers"]["console"]["level"] = "WARNING"
        config["loggers"]["visionseal"]["level"] = "INFO"
    
    return config


def setup_logging():
    """Setup logging configuration"""
    config = get_logging_config()
    logging.config.dictConfig(config)
    
    # Create logger
    logger = logging.getLogger("visionseal")
    logger.info(
        "Logging initialized",
        extra={
            "environment": settings.environment,
            "log_level": settings.api.log_level,
            "logs_dir": str(settings.logs_dir)
        }
    )
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get logger instance"""
    return logging.getLogger(f"visionseal.{name}")


# Global correlation filter for request tracking
correlation_filter = CorrelationFilter()