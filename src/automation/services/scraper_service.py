"""
Scraper Service
Handles scraper loading, configuration, and execution coordination
"""
from typing import Dict, Optional, Any, List, Callable
import importlib
from pathlib import Path

from ..constants import ScraperSource, AutomationDefaults, ErrorCodes, AutomationMessages
from ..types import ScrapingResult, ConfigDict
from core.logging.setup import get_logger
from core.config.manager import config_manager

logger = get_logger("scraper_service")


class ScraperService:
    """Service for managing scrapers"""
    
    def __init__(self):
        self.scrapers: Dict[str, Callable] = {}
        self.scraper_configs: Dict[str, Dict[str, Any]] = {}
        self.load_scrapers()
    
    def load_scrapers(self) -> None:
        """Load all available scrapers with graceful fallback"""
        logger.info("Loading scrapers...")
        
        # Try to load enhanced scrapers first
        enhanced_loaded = self._load_enhanced_scrapers()
        
        # Fallback to basic scrapers if enhanced not available
        if not enhanced_loaded:
            self._load_basic_scrapers()
        
        # Load individual scrapers as last resort
        if not self.scrapers:
            self._load_individual_scrapers()
        
        logger.info(f"Loaded {len(self.scrapers)} scrapers: {list(self.scrapers.keys())}")
    
    def get_available_scrapers(self) -> List[str]:
        """Get list of available scraper sources"""
        return list(self.scrapers.keys())
    
    def is_scraper_available(self, source: str) -> bool:
        """Check if a scraper is available"""
        return source in self.scrapers
    
    def get_scraper_function(self, source: str) -> Optional[Callable]:
        """Get scraper function for a given source"""
        return self.scrapers.get(source)
    
    def get_scraper_config(self, source: str, profile: Optional[str] = None) -> Dict[str, Any]:
        """Get merged configuration for a scraper"""
        try:
            return config_manager.get_merged_config(
                scraper=source,
                profile=profile,
                overrides={}
            )
        except Exception as e:
            logger.warning(f"Failed to get config for {source}: {e}")
            return self._get_default_config(source)
    
    def validate_scraper_config(self, source: str, config: Dict[str, Any]) -> bool:
        """Validate scraper configuration"""
        required_fields = ['max_pages', 'timeout', 'headless']
        
        for field in required_fields:
            if field not in config:
                logger.error(f"Missing required config field '{field}' for {source}")
                return False
        
        # Validate value ranges
        if config.get('max_pages', 0) <= 0:
            logger.error(f"Invalid max_pages value for {source}")
            return False
        
        if config.get('timeout', 0) <= 0:
            logger.error(f"Invalid timeout value for {source}")
            return False
        
        return True
    
    def create_scraping_task_config(
        self, 
        source: str, 
        user_config: Optional[Dict[str, Any]] = None,
        profile: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a complete task configuration for scraping"""
        base_config = self.get_scraper_config(source, profile)
        
        # Merge with user overrides
        if user_config:
            base_config.update(user_config)
        
        # Add task-specific settings
        automation_config = config_manager.get_automation_config()
        task_config = automation_config.get('task_manager', {})
        
        complete_config = {
            **base_config,
            'max_retries': task_config.get('max_retry_attempts', AutomationDefaults.MAX_RETRIES),
            'retry_delay': task_config.get('retry_delay', AutomationDefaults.RETRY_DELAY),
            'timeout': task_config.get('task_timeout', AutomationDefaults.TASK_TIMEOUT),
        }
        
        return complete_config
    
    def _load_enhanced_scrapers(self) -> bool:
        """Try to load enhanced scrapers"""
        try:
            enhanced_scrapers = {
                'ungm': 'automation.scrapers.ungm_playwright_scraper.run_ungm_scraping',
                'tunipages': 'automation.scrapers.tunipages_scraper.run_tunipages_scraping'
            }
            
            loaded_count = 0
            for source, module_path in enhanced_scrapers.items():
                try:
                    scraper_func = self._import_scraper_function(module_path)
                    if scraper_func:
                        self.scrapers[source] = scraper_func
                        loaded_count += 1
                        logger.info(f"✅ Loaded Enhanced {source.upper()} scraper")
                except ImportError as e:
                    logger.warning(f"Enhanced {source} scraper not available: {e}")
            
            if loaded_count > 0:
                logger.info(f"✅ Loaded {loaded_count} ENHANCED scrapers")
                return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Failed to load enhanced scrapers: {e}")
            return False
    
    def _load_basic_scrapers(self) -> bool:
        """Load basic scrapers as fallback"""
        try:
            basic_scrapers = {
                'ungm': 'automation.scrapers.ungm_playwright_scraper.run_ungm_scraping',
                'tunipages': 'automation.scrapers.tunipages_scraper.run_tunipages_scraping'
            }
            
            loaded_count = 0
            for source, module_path in basic_scrapers.items():
                try:
                    scraper_func = self._import_scraper_function(module_path)
                    if scraper_func:
                        self.scrapers[source] = scraper_func
                        loaded_count += 1
                        logger.info(f"⚠️ Loaded Basic {source.upper()} scraper")
                except ImportError as e:
                    logger.warning(f"Basic {source} scraper not available: {e}")
            
            if loaded_count > 0:
                logger.info(f"⚠️ Loaded {loaded_count} BASIC scrapers")
                return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Failed to load basic scrapers: {e}")
            return False
    
    def _load_individual_scrapers(self) -> None:
        """Load individual scrapers as last resort"""
        scrapers_to_try = [
            ('ungm', 'automation.scrapers.ungm_playwright_scraper.run_ungm_scraping'),
            ('tunipages', 'automation.scrapers.tunipages_scraper.run_tunipages_scraping')
        ]
        
        for source, module_path in scrapers_to_try:
            if source not in self.scrapers:  # Only load if not already loaded
                try:
                    scraper_func = self._import_scraper_function(module_path)
                    if scraper_func:
                        self.scrapers[source] = scraper_func
                        scraper_type = "Enhanced" if "enhanced" in module_path else "Basic"
                        logger.info(f"📦 Loaded {scraper_type} {source.upper()} scraper individually")
                except ImportError:
                    continue
    
    def _import_scraper_function(self, module_path: str) -> Optional[Callable]:
        """Import a scraper function from module path"""
        try:
            module_name, function_name = module_path.rsplit('.', 1)
            module = importlib.import_module(module_name)
            return getattr(module, function_name)
        except (ImportError, AttributeError) as e:
            logger.debug(f"Failed to import {module_path}: {e}")
            return None
    
    def _get_default_config(self, source: str) -> Dict[str, Any]:
        """Get default configuration for a scraper"""
        default_configs = {
            'ungm': {
                'max_pages': AutomationDefaults.MAX_PAGES,
                'timeout': AutomationDefaults.BROWSER_TIMEOUT,
                'headless': AutomationDefaults.HEADLESS,
                'request_delay': AutomationDefaults.REQUEST_DELAY,
                'retry_attempts': AutomationDefaults.MAX_RETRIES
            },
            'tunipages': {
                'max_pages': AutomationDefaults.MAX_PAGES,
                'timeout': AutomationDefaults.BROWSER_TIMEOUT,
                'headless': AutomationDefaults.HEADLESS,
                'request_delay': AutomationDefaults.REQUEST_DELAY,
                'retry_attempts': AutomationDefaults.MAX_RETRIES,
                'enable_authentication': True,
                'enable_document_processing': True
            }
        }
        
        return default_configs.get(source, {
            'max_pages': AutomationDefaults.MAX_PAGES,
            'timeout': AutomationDefaults.BROWSER_TIMEOUT,
            'headless': AutomationDefaults.HEADLESS
        })