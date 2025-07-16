"""
Health Service  
Monitors automation system health and performance
"""
from typing import Dict, Any, List
from datetime import datetime

from ..constants import HealthCheckThresholds, AutomationDefaults
from ..types import HealthStatus, AutomationMetrics
from .task_service import TaskService
from .session_service import SessionService
from core.logging.setup import get_logger

logger = get_logger("health_service")


class HealthService:
    """Service for monitoring automation system health"""
    
    def __init__(self, task_service: TaskService, session_service: SessionService):
        self.task_service = task_service
        self.session_service = session_service
        self.last_health_check = None
    
    def check_system_health(self) -> HealthStatus:
        """Perform comprehensive health check"""
        logger.debug("Performing system health check")
        
        health_status = HealthStatus(status="healthy")
        
        # Check task service health
        self._check_task_service_health(health_status)
        
        # Check session service health  
        self._check_session_service_health(health_status)
        
        # Check resource usage
        self._check_resource_health(health_status)
        
        # Check performance metrics
        self._check_performance_health(health_status)
        
        # Determine overall status
        total_tasks = health_status.metrics.total_tasks if health_status.metrics else 0
        session_metrics = self.session_service.get_session_metrics()
        total_sessions = session_metrics.get('total_sessions', 0)
        
        if len(health_status.issues) == 0:
            if total_tasks == 0 and total_sessions == 0:
                health_status.status = "idle"  # System is healthy but not actively processing
            else:
                health_status.status = "healthy"
        elif len(health_status.issues) <= 2:
            health_status.status = "degraded"
        else:
            health_status.status = "unhealthy"
        
        self.last_health_check = datetime.now()
        
        logger.info(f"Health check completed: {health_status.status} ({len(health_status.issues)} issues)")
        return health_status
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get a summary of system health"""
        health_status = self.check_system_health()
        
        return {
            'status': health_status.status,
            'is_healthy': health_status.is_healthy(),
            'issues_count': len(health_status.issues),
            'issues': health_status.issues,
            'checks': health_status.checks,
            'last_check': health_status.timestamp.isoformat(),
            'metrics': health_status.metrics.to_dict() if health_status.metrics else None
        }
    
    def _check_task_service_health(self, health_status: HealthStatus) -> None:
        """Check task service health"""
        try:
            metrics = self.task_service.get_metrics()
            health_status.metrics = metrics
            
            # Check active tasks
            if metrics.active_tasks > HealthCheckThresholds.MAX_ACTIVE_TASKS:
                health_status.add_issue(f"High number of active tasks: {metrics.active_tasks}")
            else:
                health_status.checks['active_tasks'] = True
            
            # Check failure rate (only if we have enough tasks)
            if metrics.total_tasks >= HealthCheckThresholds.MIN_TASKS_FOR_RATE_CHECK:
                if metrics.failure_rate() > HealthCheckThresholds.MAX_FAILED_RATIO:
                    health_status.add_issue(f"High failure rate: {metrics.failure_rate():.2%}")
                else:
                    health_status.checks['failure_rate'] = True
            else:
                health_status.checks['failure_rate'] = True  # Not enough data to evaluate
            
            # Check retry tasks
            if metrics.retrying_tasks > HealthCheckThresholds.MAX_RETRY_TASKS:
                health_status.add_issue(f"Many tasks retrying: {metrics.retrying_tasks}")
            else:
                health_status.checks['retry_tasks'] = True
            
            # Check success rate (only if we have enough tasks)
            if metrics.total_tasks >= HealthCheckThresholds.MIN_TASKS_FOR_RATE_CHECK:
                if metrics.success_rate() < HealthCheckThresholds.MIN_SUCCESS_RATE:
                    health_status.add_issue(f"Low success rate: {metrics.success_rate():.2%}")
                else:
                    health_status.checks['success_rate'] = True
            else:
                health_status.checks['success_rate'] = True  # Not enough data to evaluate
                
            health_status.checks['task_service'] = True
            
        except Exception as e:
            health_status.add_issue(f"Task service health check failed: {str(e)}")
            health_status.checks['task_service'] = False
    
    def _check_session_service_health(self, health_status: HealthStatus) -> None:
        """Check session service health"""
        try:
            session_metrics = self.session_service.get_session_metrics()
            
            # Check if sessions are being created (informational, not critical)
            total_sessions = session_metrics.get('total_sessions', 0)
            if total_sessions == 0:
                logger.info("No scraping sessions found - system may be idle")
                health_status.checks['sessions_exist'] = True  # Not a failure condition
            else:
                health_status.checks['sessions_exist'] = True
            
            # Check session success rate (only if we have sessions)
            session_success_rate = session_metrics.get('overall_success_rate', 0)
            if total_sessions >= 5:  # Only check if we have enough session data
                if session_success_rate < HealthCheckThresholds.MIN_SUCCESS_RATE:
                    health_status.add_issue(f"Low session success rate: {session_success_rate:.2%}")
                else:
                    health_status.checks['session_success_rate'] = True
            else:
                health_status.checks['session_success_rate'] = True  # Not enough session data
            
            health_status.checks['session_service'] = True
            
        except Exception as e:
            health_status.add_issue(f"Session service health check failed: {str(e)}")
            health_status.checks['session_service'] = False
    
    def _check_resource_health(self, health_status: HealthStatus) -> None:
        """Check system resource usage"""
        try:
            import psutil
            
            # Check memory usage
            memory = psutil.virtual_memory()
            memory_mb = memory.used / (1024 * 1024)
            
            if memory_mb > HealthCheckThresholds.MAX_MEMORY_USAGE_MB:
                health_status.add_issue(f"High memory usage: {memory_mb:.0f}MB")
            else:
                health_status.checks['memory_usage'] = True
            
            # Check CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > HealthCheckThresholds.MAX_CPU_USAGE_PERCENT:
                health_status.add_issue(f"High CPU usage: {cpu_percent:.1f}%")
            else:
                health_status.checks['cpu_usage'] = True
                
            health_status.checks['resource_monitoring'] = True
            
        except ImportError:
            # psutil not available, skip resource checks
            health_status.checks['resource_monitoring'] = False
            logger.debug("psutil not available, skipping resource checks")
        except Exception as e:
            health_status.add_issue(f"Resource health check failed: {str(e)}")
            health_status.checks['resource_monitoring'] = False
    
    def _check_performance_health(self, health_status: HealthStatus) -> None:
        """Check performance metrics"""
        try:
            if health_status.metrics:
                # Check average execution time
                avg_time = health_status.metrics.average_execution_time
                if avg_time > 300:  # 5 minutes
                    health_status.add_issue(f"Slow average execution time: {avg_time:.1f}s")
                else:
                    health_status.checks['execution_time'] = True
                
                # Check if system is processing tasks
                if health_status.metrics.tasks_created > 0 and health_status.metrics.tasks_completed == 0:
                    health_status.add_issue("Tasks created but none completed")
                else:
                    health_status.checks['task_processing'] = True
            
            health_status.checks['performance'] = True
            
        except Exception as e:
            health_status.add_issue(f"Performance health check failed: {str(e)}")
            health_status.checks['performance'] = False
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get detailed system status"""
        health = self.check_system_health()
        task_metrics = self.task_service.get_metrics()
        session_metrics = self.session_service.get_session_metrics()
        
        return {
            'overall_health': health.status,
            'timestamp': datetime.now().isoformat(),
            'task_manager': {
                'status': 'healthy' if health.checks.get('task_service', False) else 'unhealthy',
                'metrics': task_metrics.to_dict(),
                'active_workers': self.task_service.max_workers
            },
            'session_manager': {
                'status': 'healthy' if health.checks.get('session_service', False) else 'unhealthy',
                'metrics': session_metrics
            },
            'health_checks': health.checks,
            'issues': health.issues,
            'uptime_info': {
                'last_health_check': self.last_health_check.isoformat() if self.last_health_check else None
            }
        }
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate performance report"""
        task_metrics = self.task_service.get_metrics()
        session_metrics = self.session_service.get_session_metrics()
        
        return {
            'report_generated': datetime.now().isoformat(),
            'task_performance': {
                'total_tasks': task_metrics.total_tasks,
                'completion_rate': task_metrics.success_rate(),
                'average_execution_time': task_metrics.average_execution_time,
                'tasks_per_status': {
                    'completed': task_metrics.tasks_completed,
                    'failed': task_metrics.tasks_failed,
                    'active': task_metrics.active_tasks,
                    'pending': task_metrics.pending_tasks,
                    'retrying': task_metrics.retrying_tasks
                }
            },
            'session_performance': {
                'total_sessions': session_metrics.get('total_sessions', 0),
                'tenders_found': session_metrics.get('total_tenders_found', 0),
                'tenders_processed': session_metrics.get('total_tenders_processed', 0),
                'overall_success_rate': session_metrics.get('overall_success_rate', 0),
                'by_source': session_metrics.get('source_breakdown', {}),
                'by_status': session_metrics.get('status_breakdown', {})
            },
            'recommendations': self._generate_recommendations(task_metrics, session_metrics)
        }
    
    def _generate_recommendations(self, task_metrics: AutomationMetrics, session_metrics: Dict[str, Any]) -> List[str]:
        """Generate performance recommendations"""
        recommendations = []
        
        # Task-related recommendations
        if task_metrics.failure_rate() > 0.3:
            recommendations.append("High task failure rate detected. Review error logs and improve error handling.")
        
        if task_metrics.average_execution_time > 180:  # 3 minutes
            recommendations.append("Tasks are taking longer than expected. Consider optimizing scraper performance.")
        
        if task_metrics.retrying_tasks > 3:
            recommendations.append("Many tasks are retrying. Check network connectivity and target site availability.")
        
        # Session-related recommendations
        session_success_rate = session_metrics.get('overall_success_rate', 0)
        if session_success_rate < 0.7:
            recommendations.append("Low session success rate. Review scraper configurations and target site changes.")
        
        total_tenders = session_metrics.get('total_tenders_found', 0)
        if total_tenders == 0:
            recommendations.append("No tenders found in recent sessions. Verify scraper functionality and target sites.")
        
        # Resource recommendations
        if task_metrics.active_tasks > 8:
            recommendations.append("High number of active tasks. Consider increasing worker pool size.")
        
        return recommendations