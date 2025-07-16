"""
Automation Manager
Clean, readable orchestrator for all automation services
"""
from typing import Dict, List, Optional, Any
import threading
import time
from datetime import datetime

from .constants import TaskPriority, TaskStatus, AutomationDefaults
from .types import AutomationMetrics, HealthStatus
from .services import TaskService, ScraperService, SessionService, HealthService
from core.logging.setup import get_logger

logger = get_logger("automation_manager")


class AutomationManager:
    """
    Main automation manager that orchestrates all automation services
    
    This class provides a clean, high-level interface for:
    - Creating and managing scraping sessions
    - Monitoring system health
    - Coordinating background tasks
    - Managing scrapers and configurations
    """
    
    def __init__(self, max_workers: Optional[int] = None):
        # Initialize services
        self.task_service = TaskService(max_workers)
        self.scraper_service = ScraperService()
        self.session_service = SessionService(self.task_service, self.scraper_service)
        self.health_service = HealthService(self.task_service, self.session_service)
        
        # Background scheduler
        self.scheduler_running = False
        self.scheduler_thread: Optional[threading.Thread] = None
        
        logger.info("Automation Manager initialized successfully")
    
    # === High-Level Public Interface ===
    
    def start_scraping(
        self,
        source: str,
        user_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        priority: TaskPriority = TaskPriority.HIGH,
        profile: Optional[str] = None
    ) -> Optional[str]:
        """
        Start a new scraping session
        
        Args:
            source: Scraper source ('ungm', 'tunipages')
            user_id: Optional user ID for tracking
            config: Optional configuration overrides
            priority: Task priority level
            profile: Optional configuration profile
            
        Returns:
            Session ID if successful, None if failed
        """
        logger.info(f"Starting scraping session for {source} (user: {user_id})")
        
        # Create session
        session_id = self.session_service.create_scraping_session(
            source=source,
            user_id=user_id,
            config=config,
            priority=priority,
            profile=profile
        )
        
        if not session_id:
            logger.error(f"Failed to create scraping session for {source}")
            return None
        
        # Start the session
        success = self.session_service.start_session(session_id)
        if success:
            logger.info(f"Scraping session {session_id} started successfully")
            return session_id
        else:
            logger.error(f"Failed to start scraping session {session_id}")
            return None
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get detailed status of a scraping session"""
        return self.session_service.get_session_status(session_id)
    
    def cancel_session(self, session_id: str) -> bool:
        """Cancel a running scraping session"""
        return self.session_service.cancel_session(session_id)
    
    def list_sessions(
        self,
        user_id: Optional[str] = None,
        source: Optional[str] = None,
        status: Optional[TaskStatus] = None
    ) -> List[Dict[str, Any]]:
        """List scraping sessions with optional filters"""
        return self.session_service.list_sessions(user_id, source, status)
    
    def start_all_scrapers(self, config: Optional[Dict[str, Any]] = None) -> List[str]:
        """Start scraping sessions for all available scrapers"""
        session_ids = []
        available_scrapers = self.scraper_service.get_available_scrapers()
        
        for source in available_scrapers:
            session_id = self.start_scraping(
                source=source,
                config=config,
                priority=TaskPriority.HIGH
            )
            if session_id:
                session_ids.append(session_id)
        
        logger.info(f"Started {len(session_ids)} scraping sessions")
        return session_ids
    
    # === System Management ===
    
    def get_system_health(self) -> HealthStatus:
        """Get current system health status"""
        return self.health_service.check_system_health()
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get system health summary"""
        return self.health_service.get_health_summary()
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get detailed system status"""
        return self.health_service.get_system_status()
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get performance analysis report"""
        return self.health_service.get_performance_report()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive system metrics"""
        task_metrics = self.task_service.get_metrics()
        session_metrics = self.session_service.get_session_metrics()
        
        return {
            'task_metrics': task_metrics.to_dict(),
            'session_metrics': session_metrics,
            'combined_metrics': {
                'total_operations': task_metrics.total_tasks + session_metrics.get('total_sessions', 0),
                'overall_success_rate': (
                    task_metrics.success_rate() + session_metrics.get('overall_success_rate', 0)
                ) / 2,
                'system_health': self.get_health_summary()['status']
            }
        }
    
    # === Configuration and Scrapers ===
    
    def get_available_scrapers(self) -> List[str]:
        """Get list of available scraper sources"""
        return self.scraper_service.get_available_scrapers()
    
    def get_scraper_capabilities(self) -> Dict[str, Any]:
        """Get information about scraper capabilities"""
        available_scrapers = self.scraper_service.get_available_scrapers()
        
        capabilities = {
            'available_sources': available_scrapers,
            'total_scrapers': len(available_scrapers),
            'features': {
                'enhanced_automation': any('enhanced' in source for source in available_scrapers),
                'document_processing': True,  # Available in enhanced scrapers
                'authentication': True,  # TuniPages has auth
                'real_time_monitoring': True,
                'configurable_profiles': True
            },
            'source_details': {}
        }
        
        # Get details for each scraper
        for source in available_scrapers:
            config = self.scraper_service.get_scraper_config(source)
            capabilities['source_details'][source] = {
                'max_pages': config.get('max_pages', 'Unknown'),
                'timeout': config.get('timeout', 'Unknown'),
                'authentication_required': config.get('enable_authentication', False),
                'document_processing': config.get('enable_document_processing', False)
            }
        
        return capabilities
    
    # === Background Operations ===
    
    def start_scheduler(self) -> None:
        """Start the background scheduler for maintenance tasks"""
        if self.scheduler_running:
            logger.warning("Scheduler is already running")
            return
        
        self.scheduler_running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        logger.info("Background scheduler started")
    
    def stop_scheduler(self) -> None:
        """Stop the background scheduler"""
        if not self.scheduler_running:
            return
        
        self.scheduler_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        logger.info("Background scheduler stopped")
    
    def cleanup_old_data(self) -> Dict[str, int]:
        """Clean up old tasks and sessions"""
        logger.info("Starting cleanup of old data")
        
        # Clean up old tasks
        tasks_cleaned = self.task_service.cleanup_completed_tasks(
            hours_old=AutomationDefaults.CLEANUP_HOURS
        )
        
        # Clean up old sessions
        sessions_cleaned = self.session_service.cleanup_old_sessions(
            hours_old=AutomationDefaults.CLEANUP_FAILED_HOURS
        )
        
        cleanup_result = {
            'tasks_cleaned': tasks_cleaned,
            'sessions_cleaned': sessions_cleaned,
            'total_cleaned': tasks_cleaned + sessions_cleaned
        }
        
        logger.info(f"Cleanup completed: {cleanup_result}")
        return cleanup_result
    
    # === Lifecycle Management ===
    
    def shutdown(self) -> None:
        """Gracefully shutdown the automation manager"""
        logger.info("Shutting down Automation Manager...")
        
        # Stop scheduler first
        self.stop_scheduler()
        
        # Cancel all active sessions
        active_sessions = self.list_sessions(status=TaskStatus.RUNNING)
        for session in active_sessions:
            self.cancel_session(session['session_id'])
        
        # Shutdown task service
        self.task_service.shutdown()
        
        logger.info("Automation Manager shutdown complete")
    
    def restart_services(self) -> bool:
        """Restart all services (useful for configuration changes)"""
        try:
            logger.info("Restarting automation services...")
            
            # Stop scheduler
            self.stop_scheduler()
            
            # Reload scrapers
            self.scraper_service.load_scrapers()
            
            # Restart scheduler
            self.start_scheduler()
            
            logger.info("Services restarted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restart services: {str(e)}")
            return False
    
    # === Private Methods ===
    
    def _scheduler_loop(self) -> None:
        """Main scheduler loop for background maintenance"""
        logger.info("Scheduler loop started")
        
        while self.scheduler_running:
            try:
                # Perform health check
                health = self.health_service.check_system_health()
                if not health.is_healthy():
                    logger.warning(f"System health degraded: {health.issues}")
                
                # Cleanup old data periodically (every hour)
                current_time = time.time()
                if not hasattr(self, '_last_cleanup') or (current_time - self._last_cleanup) > 3600:
                    self.cleanup_old_data()
                    self._last_cleanup = current_time
                
                # Sleep until next check
                time.sleep(AutomationDefaults.SCHEDULER_INTERVAL)
                
            except Exception as e:
                logger.error(f"Scheduler error: {str(e)}")
                time.sleep(60)  # Wait longer on error
        
        logger.info("Scheduler loop stopped")


# Global automation manager instance
automation_manager = AutomationManager()

# Start scheduler automatically
automation_manager.start_scheduler()