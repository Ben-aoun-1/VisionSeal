"""
Health check implementations for all system components
"""
import asyncio
import time
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from enum import Enum

from core.logging.setup import get_logger

logger = get_logger("health_checks")


class HealthStatus(str, Enum):
    """Health status enumeration"""
    HEALTHY = "healthy"
    DEGRADED = "degraded" 
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class HealthCheckResult:
    """Health check result container"""
    
    def __init__(
        self,
        status: HealthStatus,
        response_time_ms: Optional[float] = None,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ):
        self.status = status
        self.response_time_ms = response_time_ms
        self.message = message
        self.details = details or {}
        self.error = error
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        result = {
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat(),
        }
        
        if self.response_time_ms is not None:
            result["response_time_ms"] = round(self.response_time_ms, 2)
        
        if self.message:
            result["message"] = self.message
            
        if self.error:
            result["error"] = self.error
            
        if self.details:
            result["details"] = self.details
            
        return result


class DatabaseHealthChecker:
    """Database connectivity health checker"""
    
    @staticmethod
    async def check_supabase() -> HealthCheckResult:
        """Check Supabase database connectivity"""
        try:
            start_time = time.time()
            
            # Import here to avoid circular imports
            from core.database.supabase_client import supabase_manager
            
            # Perform actual connectivity test
            client = supabase_manager.get_client()
            
            # Simple query to test connectivity
            response = client.table('tenders').select('id').limit(1).execute()
            
            response_time = (time.time() - start_time) * 1000
            
            if response.data is not None:
                return HealthCheckResult(
                    status=HealthStatus.HEALTHY,
                    response_time_ms=response_time,
                    message="Database connection successful",
                    details={
                        "provider": "Supabase",
                        "query_executed": "SELECT id FROM tenders LIMIT 1"
                    }
                )
            else:
                return HealthCheckResult(
                    status=HealthStatus.DEGRADED,
                    response_time_ms=response_time,
                    message="Database query returned no data structure",
                    error="Unexpected response format"
                )
                
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                message="Database connection failed",
                error=str(e),
                details={"provider": "Supabase"}
            )
    
    @staticmethod
    async def check_alternative_db() -> HealthCheckResult:
        """Check alternative database if available"""
        try:
            # Check if SQLAlchemy connection is available
            from core.database.repositories import TenderRepository
            
            # This would require a database session
            # For now, return unknown since we don't have session management
            return HealthCheckResult(
                status=HealthStatus.UNKNOWN,
                message="SQLAlchemy connection not configured",
                details={"provider": "SQLAlchemy", "note": "Session management required"}
            )
            
        except ImportError:
            return HealthCheckResult(
                status=HealthStatus.UNKNOWN,
                message="Alternative database not available"
            )


class CacheHealthChecker:
    """Redis/Cache connectivity health checker"""
    
    @staticmethod
    async def check_redis() -> HealthCheckResult:
        """Check Redis connectivity"""
        try:
            import redis
            import os
            
            start_time = time.time()
            
            # Get Redis connection details from environment
            redis_url = os.getenv('REDIS_URL')
            redis_host = os.getenv('REDIS_HOST', 'localhost')
            redis_port = int(os.getenv('REDIS_PORT', 6379))
            redis_password = os.getenv('REDIS_PASSWORD')
            
            if redis_url:
                # Use Redis URL if available
                r = redis.from_url(redis_url)
            else:
                # Use individual connection parameters
                r = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    password=redis_password,
                    socket_timeout=5,
                    socket_connect_timeout=5
                )
            
            # Test connectivity with ping
            result = r.ping()
            response_time = (time.time() - start_time) * 1000
            
            if result:
                # Get additional info
                info = r.info()
                return HealthCheckResult(
                    status=HealthStatus.HEALTHY,
                    response_time_ms=response_time,
                    message="Redis connection successful",
                    details={
                        "version": info.get('redis_version'),
                        "memory_used": info.get('used_memory_human'),
                        "connected_clients": info.get('connected_clients')
                    }
                )
            else:
                return HealthCheckResult(
                    status=HealthStatus.UNHEALTHY,
                    response_time_ms=response_time,
                    message="Redis ping failed"
                )
                
        except ImportError:
            return HealthCheckResult(
                status=HealthStatus.UNKNOWN,
                message="Redis client not installed",
                details={"note": "Install redis package for Redis support"}
            )
        except Exception as e:
            logger.error(f"Redis health check failed: {str(e)}")
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                message="Redis connection failed",
                error=str(e)
            )


class VectorStoreHealthChecker:
    """Weaviate/Vector store connectivity health checker"""
    
    @staticmethod
    async def check_weaviate() -> HealthCheckResult:
        """Check Weaviate connectivity"""
        try:
            import weaviate
            import os
            
            start_time = time.time()
            
            # Get Weaviate connection details
            weaviate_url = os.getenv('WEAVIATE_URL', 'http://localhost:8080')
            weaviate_api_key = os.getenv('WEAVIATE_API_KEY')
            
            # Create client
            if weaviate_api_key:
                client = weaviate.Client(
                    url=weaviate_url,
                    auth_client_secret=weaviate.auth.AuthApiKey(api_key=weaviate_api_key),
                    timeout_config=(5, 15)
                )
            else:
                client = weaviate.Client(
                    url=weaviate_url,
                    timeout_config=(5, 15)
                )
            
            # Test connectivity
            is_ready = client.is_ready()
            response_time = (time.time() - start_time) * 1000
            
            if is_ready:
                # Get cluster info
                meta = client.get_meta()
                return HealthCheckResult(
                    status=HealthStatus.HEALTHY,
                    response_time_ms=response_time,
                    message="Weaviate connection successful",
                    details={
                        "version": meta.get('version'),
                        "hostname": meta.get('hostname'),
                        "modules": meta.get('modules', {}).keys() if meta.get('modules') else []
                    }
                )
            else:
                return HealthCheckResult(
                    status=HealthStatus.UNHEALTHY,
                    response_time_ms=response_time,
                    message="Weaviate not ready"
                )
                
        except ImportError:
            return HealthCheckResult(
                status=HealthStatus.UNKNOWN,
                message="Weaviate client not installed",
                details={"note": "Install weaviate-client package for Weaviate support"}
            )
        except Exception as e:
            logger.error(f"Weaviate health check failed: {str(e)}")
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                message="Weaviate connection failed",
                error=str(e)
            )


class AutomationHealthChecker:
    """Automation system health checker"""
    
    @staticmethod
    async def check_automation_system() -> HealthCheckResult:
        """Check automation system health"""
        try:
            start_time = time.time()
            
            # Import automation manager
            from automation.task_manager import automation_manager
            
            # Get system metrics
            metrics = automation_manager.get_metrics()
            response_time = (time.time() - start_time) * 1000
            
            # Determine health based on metrics
            total_tasks = metrics.get('tasks_created', 0)
            failed_tasks = metrics.get('tasks_failed', 0)
            active_tasks = metrics.get('active_tasks', 0)
            
            if total_tasks == 0:
                status = HealthStatus.HEALTHY
                message = "Automation system ready"
            elif failed_tasks > 0 and total_tasks > 0:
                failure_rate = failed_tasks / total_tasks
                if failure_rate > 0.5:
                    status = HealthStatus.DEGRADED
                    message = f"High failure rate: {failure_rate:.1%}"
                elif failure_rate > 0.1:
                    status = HealthStatus.DEGRADED  
                    message = f"Moderate failure rate: {failure_rate:.1%}"
                else:
                    status = HealthStatus.HEALTHY
                    message = "Automation system operational"
            else:
                status = HealthStatus.HEALTHY
                message = "Automation system operational"
            
            return HealthCheckResult(
                status=status,
                response_time_ms=response_time,
                message=message,
                details={
                    "total_tasks": total_tasks,
                    "active_tasks": active_tasks,
                    "failed_tasks": failed_tasks,
                    "pending_tasks": metrics.get('pending_tasks', 0),
                    "completed_tasks": metrics.get('tasks_completed', 0)
                }
            )
            
        except Exception as e:
            logger.error(f"Automation health check failed: {str(e)}")
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                message="Automation system check failed",
                error=str(e)
            )


class AIHealthChecker:
    """AI system health checker"""
    
    @staticmethod
    async def check_ai_system() -> HealthCheckResult:
        """Check AI system health"""
        try:
            import os
            
            start_time = time.time()
            
            # Check if OpenAI API key is configured
            openai_key = os.getenv('OPENAI_API_KEY')
            
            if not openai_key:
                return HealthCheckResult(
                    status=HealthStatus.UNKNOWN,
                    message="OpenAI API key not configured",
                    details={"note": "Set OPENAI_API_KEY environment variable"}
                )
            
            # Test OpenAI connectivity (simple check)
            try:
                import openai
                
                # Set API key
                openai.api_key = openai_key
                
                # Simple API call to check connectivity
                # Note: This is a minimal check to avoid costs
                models = openai.Model.list()
                response_time = (time.time() - start_time) * 1000
                
                if models and len(models.data) > 0:
                    available_models = [model.id for model in models.data[:5]]
                    return HealthCheckResult(
                        status=HealthStatus.HEALTHY,
                        response_time_ms=response_time,
                        message="OpenAI API accessible",
                        details={
                            "provider": "OpenAI",
                            "available_models": available_models,
                            "total_models": len(models.data)
                        }
                    )
                else:
                    return HealthCheckResult(
                        status=HealthStatus.DEGRADED,
                        response_time_ms=response_time,
                        message="OpenAI API responded but no models available"
                    )
                    
            except ImportError:
                return HealthCheckResult(
                    status=HealthStatus.UNKNOWN,
                    message="OpenAI client not installed",
                    details={"note": "Install openai package for AI support"}
                )
                
        except Exception as e:
            logger.error(f"AI health check failed: {str(e)}")
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                message="AI system check failed",
                error=str(e)
            )


class ExternalServiceHealthChecker:
    """External service health checker"""
    
    @staticmethod
    async def check_ungm_availability() -> HealthCheckResult:
        """Check UNGM website availability"""
        try:
            import aiohttp
            
            start_time = time.time()
            timeout = aiohttp.ClientTimeout(total=10)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get('https://www.ungm.org') as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        return HealthCheckResult(
                            status=HealthStatus.HEALTHY,
                            response_time_ms=response_time,
                            message="UNGM website accessible",
                            details={"url": "https://www.ungm.org", "status_code": response.status}
                        )
                    else:
                        return HealthCheckResult(
                            status=HealthStatus.DEGRADED,
                            response_time_ms=response_time,
                            message=f"UNGM returned status {response.status}",
                            details={"url": "https://www.ungm.org", "status_code": response.status}
                        )
                        
        except ImportError:
            return HealthCheckResult(
                status=HealthStatus.UNKNOWN,
                message="aiohttp not available for external checks"
            )
        except Exception as e:
            logger.error(f"UNGM health check failed: {str(e)}")
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                message="UNGM website not accessible",
                error=str(e)
            )
    
    @staticmethod
    async def check_tunipages_availability() -> HealthCheckResult:
        """Check TuniPages website availability"""
        try:
            import aiohttp
            
            start_time = time.time()
            timeout = aiohttp.ClientTimeout(total=10)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get('https://www.tunipages.com') as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        return HealthCheckResult(
                            status=HealthStatus.HEALTHY,
                            response_time_ms=response_time,
                            message="TuniPages website accessible",
                            details={"url": "https://www.tunipages.com", "status_code": response.status}
                        )
                    else:
                        return HealthCheckResult(
                            status=HealthStatus.DEGRADED,
                            response_time_ms=response_time,
                            message=f"TuniPages returned status {response.status}",
                            details={"url": "https://www.tunipages.com", "status_code": response.status}
                        )
                        
        except ImportError:
            return HealthCheckResult(
                status=HealthStatus.UNKNOWN,
                message="aiohttp not available for external checks"
            )
        except Exception as e:
            logger.error(f"TuniPages health check failed: {str(e)}")
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                message="TuniPages website not accessible",
                error=str(e)
            )


class HealthCheckManager:
    """Centralized health check manager"""
    
    def __init__(self):
        self.db_checker = DatabaseHealthChecker()
        self.cache_checker = CacheHealthChecker()
        self.vector_checker = VectorStoreHealthChecker()
        self.automation_checker = AutomationHealthChecker()
        self.ai_checker = AIHealthChecker()
        self.external_checker = ExternalServiceHealthChecker()
    
    async def check_all_services(self, include_external: bool = False) -> Dict[str, Dict[str, Any]]:
        """Check all services and return comprehensive status"""
        logger.info("Starting comprehensive health check")
        
        # Core service checks (run in parallel)
        core_checks = await asyncio.gather(
            self.db_checker.check_supabase(),
            self.cache_checker.check_redis(), 
            self.vector_checker.check_weaviate(),
            self.automation_checker.check_automation_system(),
            self.ai_checker.check_ai_system(),
            return_exceptions=True
        )
        
        # Map results to service names
        services = {
            "database": core_checks[0] if not isinstance(core_checks[0], Exception) else HealthCheckResult(HealthStatus.UNHEALTHY, error=str(core_checks[0])),
            "redis": core_checks[1] if not isinstance(core_checks[1], Exception) else HealthCheckResult(HealthStatus.UNHEALTHY, error=str(core_checks[1])),
            "weaviate": core_checks[2] if not isinstance(core_checks[2], Exception) else HealthCheckResult(HealthStatus.UNHEALTHY, error=str(core_checks[2])),
            "automation": core_checks[3] if not isinstance(core_checks[3], Exception) else HealthCheckResult(HealthStatus.UNHEALTHY, error=str(core_checks[3])),
            "ai": core_checks[4] if not isinstance(core_checks[4], Exception) else HealthCheckResult(HealthStatus.UNHEALTHY, error=str(core_checks[4]))
        }
        
        # External service checks (if requested)
        if include_external:
            external_checks = await asyncio.gather(
                self.external_checker.check_ungm_availability(),
                self.external_checker.check_tunipages_availability(),
                return_exceptions=True
            )
            
            services.update({
                "ungm": external_checks[0] if not isinstance(external_checks[0], Exception) else HealthCheckResult(HealthStatus.UNHEALTHY, error=str(external_checks[0])),
                "tunipages": external_checks[1] if not isinstance(external_checks[1], Exception) else HealthCheckResult(HealthStatus.UNHEALTHY, error=str(external_checks[1]))
            })
        
        # Convert results to dict format
        result = {}
        for service_name, check_result in services.items():
            result[service_name] = check_result.to_dict()
        
        logger.info(f"Health check completed for {len(result)} services")
        return result
    
    def determine_overall_status(self, services: Dict[str, Dict[str, Any]]) -> str:
        """Determine overall system health status"""
        statuses = [service.get('status', 'unknown') for service in services.values()]
        
        if 'unhealthy' in statuses:
            return 'unhealthy'
        elif 'degraded' in statuses:
            return 'degraded'
        elif all(status in ['healthy', 'unknown'] for status in statuses):
            return 'healthy'
        else:
            return 'unknown'


# Global health check manager instance
health_manager = HealthCheckManager()