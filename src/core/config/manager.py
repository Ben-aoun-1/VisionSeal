"""
Configuration Manager for VisionSeal
Provides dynamic configuration management, validation, and hot-reload capabilities
"""
import os
import json
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
from typing import Dict, Any, Optional, Union, List
from pathlib import Path
from datetime import datetime
import logging

from pydantic import ValidationError
from core.config.settings import settings, AutomationSettings
from core.logging.setup import get_logger

logger = get_logger("config_manager")


class ConfigurationError(Exception):
    """Configuration-related errors"""
    pass


class ConfigManager:
    """Dynamic configuration manager"""
    
    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path("config")
        self.config_dir.mkdir(exist_ok=True)
        
        # Configuration files
        self.automation_config_file = self.config_dir / "automation.json"
        self.profiles_config_file = self.config_dir / "profiles.json"
        self.overrides_config_file = self.config_dir / "overrides.json"
        
        # In-memory configuration cache
        self._config_cache: Dict[str, Any] = {}
        self._file_timestamps: Dict[str, float] = {}
        
        # Load initial configurations
        self._load_configurations()
        
        logger.info(f"Configuration Manager initialized with config dir: {self.config_dir}")
    
    def _load_configurations(self):
        """Load all configuration files"""
        try:
            self._load_automation_config()
            self._load_profiles_config()
            self._load_overrides_config()
        except Exception as e:
            logger.warning(f"Error loading configurations: {str(e)}")
    
    def _load_automation_config(self):
        """Load automation-specific configuration"""
        if self.automation_config_file.exists():
            try:
                with open(self.automation_config_file, 'r') as f:
                    automation_config = json.load(f)
                
                self._config_cache['automation'] = automation_config
                self._file_timestamps['automation'] = self.automation_config_file.stat().st_mtime
                
                logger.info("Loaded automation configuration")
            except Exception as e:
                logger.error(f"Failed to load automation config: {str(e)}")
        else:
            # Create default automation config
            self._create_default_automation_config()
    
    def _create_default_automation_config(self):
        """Create default automation configuration file"""
        default_config = {
            "scrapers": {
                "ungm": {
                    "enabled": True,
                    "max_pages": 10,
                    "request_delay": 2,
                    "timeout": 30,
                    "retry_attempts": 3,
                    "priority_keywords": [
                        "consulting", "conseil", "advisory", "technical assistance",
                        "capacity building", "training", "formation", "étude"
                    ],
                    "target_countries": [
                        # North Africa
                        "Tunisia", "Morocco", "Algeria", "Egypt", "Libya", "Sudan",
                        
                        # West Africa  
                        "Nigeria", "Ghana", "Senegal", "Mali", "Burkina Faso", "Niger",
                        "Guinea", "Sierra Leone", "Liberia", "Ivory Coast", "Benin", "Togo",
                        
                        # East Africa
                        "Kenya", "Ethiopia", "Tanzania", "Uganda", "Rwanda", "Burundi",
                        "Somalia", "Madagascar", "Mauritius",
                        
                        # Central Africa
                        "Democratic Republic of Congo", "Congo", "Cameroon", "Chad", "Gabon",
                        "Central African Republic",
                        
                        # Southern Africa
                        "South Africa", "Botswana", "Namibia", "Zimbabwe", "Zambia",
                        "Angola", "Mozambique", "Malawi", "Lesotho"
                    ]
                },
                "tunipages": {
                    "enabled": True,
                    "max_pages": 10,
                    "request_delay": 2,
                    "timeout": 30,
                    "retry_attempts": 3,
                    "priority_keywords": [
                        "consulting", "conseil", "management", "étude",
                        "formation", "expertise", "audit", "strategy"
                    ],
                    "focus_regions": ["Africa", "African Continent", "Sub-Saharan Africa", "North Africa"]
                }
            },
            "task_manager": {
                "max_workers": 4,
                "scheduler_interval": 30,
                "cleanup_interval": 3600,
                "max_retry_attempts": 3,
                "retry_delay": 300,
                "task_timeout": 3600
            },
            "performance": {
                "max_concurrent_scrapers": 2,
                "memory_threshold_mb": 1024,
                "cpu_threshold_percent": 80,
                "disk_threshold_percent": 85
            },
            "monitoring": {
                "enable_metrics": True,
                "metrics_retention_days": 30,
                "alert_failure_threshold": 0.5,
                "health_check_interval": 60
            }
        }
        
        self._save_config_file(self.automation_config_file, default_config)
        self._config_cache['automation'] = default_config
        logger.info("Created default automation configuration")
    
    def _load_profiles_config(self):
        """Load scraping profiles configuration"""
        if self.profiles_config_file.exists():
            try:
                with open(self.profiles_config_file, 'r') as f:
                    profiles_config = json.load(f)
                
                self._config_cache['profiles'] = profiles_config
                self._file_timestamps['profiles'] = self.profiles_config_file.stat().st_mtime
                
                logger.info("Loaded profiles configuration")
            except Exception as e:
                logger.error(f"Failed to load profiles config: {str(e)}")
        else:
            self._create_default_profiles_config()
    
    def _create_default_profiles_config(self):
        """Create default profiles configuration"""
        default_profiles = {
            "topaza_africa": {
                "name": "Topaza Africa Focus", 
                "description": "Optimized for Topaza.net business across Africa",
                "settings": {
                    "max_pages": 20,
                    "priority_countries": [
                        "Nigeria", "South Africa", "Kenya", "Ghana", "Egypt", 
                        "Morocco", "Tunisia", "Algeria", "Ethiopia", "Tanzania"
                    ],
                    "priority_sectors": [
                        "management consulting", "business development",
                        "training", "technical studies", "digital transformation"
                    ],
                    "min_relevance_score": 30.0,
                    "urgent_deadline_days": 10
                }
            },
            "development": {
                "name": "Development Profile",
                "description": "Fast testing with limited scope",
                "settings": {
                    "max_pages": 2,
                    "headless": False,
                    "request_delay": 1,
                    "timeout": 15
                }
            },
            "production": {
                "name": "Production Profile",
                "description": "Full-scale production scraping",
                "settings": {
                    "max_pages": 50,
                    "headless": True,
                    "request_delay": 3,
                    "timeout": 60,
                    "enable_monitoring": True
                }
            }
        }
        
        self._save_config_file(self.profiles_config_file, default_profiles)
        self._config_cache['profiles'] = default_profiles
        logger.info("Created default profiles configuration")
    
    def _load_overrides_config(self):
        """Load configuration overrides"""
        if self.overrides_config_file.exists():
            try:
                with open(self.overrides_config_file, 'r') as f:
                    overrides_config = json.load(f)
                
                self._config_cache['overrides'] = overrides_config
                self._file_timestamps['overrides'] = self.overrides_config_file.stat().st_mtime
                
                logger.info("Loaded overrides configuration")
            except Exception as e:
                logger.error(f"Failed to load overrides config: {str(e)}")
        else:
            self._config_cache['overrides'] = {}
    
    def _save_config_file(self, file_path: Path, config: Dict[str, Any]):
        """Save configuration to file"""
        try:
            with open(file_path, 'w') as f:
                json.dump(config, f, indent=2, default=str)
            
            # Update timestamp
            config_type = file_path.stem
            self._file_timestamps[config_type] = file_path.stat().st_mtime
            
        except Exception as e:
            logger.error(f"Failed to save config file {file_path}: {str(e)}")
            raise ConfigurationError(f"Failed to save configuration: {str(e)}")
    
    def get_automation_config(self, scraper: Optional[str] = None) -> Dict[str, Any]:
        """Get automation configuration for specific scraper or all"""
        self._refresh_config_if_needed('automation')
        
        automation_config = self._config_cache.get('automation', {})
        
        if scraper:
            return automation_config.get('scrapers', {}).get(scraper, {})
        
        return automation_config
    
    def get_profile_config(self, profile_name: str) -> Dict[str, Any]:
        """Get configuration for a specific profile"""
        self._refresh_config_if_needed('profiles')
        
        profiles = self._config_cache.get('profiles', {})
        
        if profile_name not in profiles:
            raise ConfigurationError(f"Profile '{profile_name}' not found")
        
        return profiles[profile_name]
    
    def get_merged_config(
        self,
        scraper: str,
        profile: Optional[str] = None,
        overrides: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get merged configuration from multiple sources"""
        
        # Start with base automation settings
        config = dict(settings.automation.__dict__)
        
        # Apply automation config file settings
        automation_config = self.get_automation_config(scraper)
        config.update(automation_config)
        
        # Apply profile settings if specified
        if profile:
            try:
                profile_config = self.get_profile_config(profile)
                profile_settings = profile_config.get('settings', {})
                config.update(profile_settings)
            except ConfigurationError as e:
                logger.warning(f"Profile error: {str(e)}")
        
        # Apply global overrides
        overrides_config = self._config_cache.get('overrides', {})
        if overrides_config:
            config.update(overrides_config)
        
        # Apply local overrides
        if overrides:
            config.update(overrides)
        
        return config
    
    def update_automation_config(self, scraper: str, config: Dict[str, Any]):
        """Update automation configuration for a scraper"""
        automation_config = self._config_cache.get('automation', {})
        
        if 'scrapers' not in automation_config:
            automation_config['scrapers'] = {}
        
        automation_config['scrapers'][scraper] = config
        self._config_cache['automation'] = automation_config
        
        # Save to file
        self._save_config_file(self.automation_config_file, automation_config)
        
        logger.info(f"Updated automation config for {scraper}")
    
    def create_profile(self, name: str, description: str, settings: Dict[str, Any]):
        """Create a new scraping profile"""
        profiles = self._config_cache.get('profiles', {})
        
        profiles[name] = {
            'name': name,
            'description': description,
            'settings': settings,
            'created_at': datetime.now().isoformat()
        }
        
        self._config_cache['profiles'] = profiles
        self._save_config_file(self.profiles_config_file, profiles)
        
        logger.info(f"Created new profile: {name}")
    
    def delete_profile(self, name: str):
        """Delete a scraping profile"""
        profiles = self._config_cache.get('profiles', {})
        
        if name not in profiles:
            raise ConfigurationError(f"Profile '{name}' not found")
        
        del profiles[name]
        self._config_cache['profiles'] = profiles
        self._save_config_file(self.profiles_config_file, profiles)
        
        logger.info(f"Deleted profile: {name}")
    
    def set_overrides(self, overrides: Dict[str, Any]):
        """Set global configuration overrides"""
        self._config_cache['overrides'] = overrides
        self._save_config_file(self.overrides_config_file, overrides)
        
        logger.info("Updated global configuration overrides")
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate configuration against schema"""
        try:
            # Try to create AutomationSettings with the config
            AutomationSettings(**config)
            return True
        except ValidationError as e:
            logger.error(f"Configuration validation failed: {str(e)}")
            return False
    
    def _refresh_config_if_needed(self, config_type: str):
        """Refresh configuration if file has been modified"""
        file_map = {
            'automation': self.automation_config_file,
            'profiles': self.profiles_config_file,
            'overrides': self.overrides_config_file
        }
        
        config_file = file_map.get(config_type)
        if not config_file or not config_file.exists():
            return
        
        current_mtime = config_file.stat().st_mtime
        cached_mtime = self._file_timestamps.get(config_type, 0)
        
        if current_mtime > cached_mtime:
            logger.info(f"Reloading {config_type} configuration (file modified)")
            
            if config_type == 'automation':
                self._load_automation_config()
            elif config_type == 'profiles':
                self._load_profiles_config()
            elif config_type == 'overrides':
                self._load_overrides_config()
    
    def get_all_profiles(self) -> Dict[str, Any]:
        """Get all available profiles"""
        self._refresh_config_if_needed('profiles')
        return self._config_cache.get('profiles', {})
    
    def export_config(self, output_file: Path):
        """Export all configurations to a single file"""
        try:
            all_config = {
                'automation': self._config_cache.get('automation', {}),
                'profiles': self._config_cache.get('profiles', {}),
                'overrides': self._config_cache.get('overrides', {}),
                'exported_at': datetime.now().isoformat()
            }
            
            with open(output_file, 'w') as f:
                json.dump(all_config, f, indent=2, default=str)
            
            logger.info(f"Exported configuration to {output_file}")
            
        except Exception as e:
            logger.error(f"Failed to export configuration: {str(e)}")
            raise ConfigurationError(f"Export failed: {str(e)}")
    
    def import_config(self, input_file: Path):
        """Import configurations from file"""
        try:
            with open(input_file, 'r') as f:
                imported_config = json.load(f)
            
            # Update each configuration type
            if 'automation' in imported_config:
                self._config_cache['automation'] = imported_config['automation']
                self._save_config_file(self.automation_config_file, imported_config['automation'])
            
            if 'profiles' in imported_config:
                self._config_cache['profiles'] = imported_config['profiles']
                self._save_config_file(self.profiles_config_file, imported_config['profiles'])
            
            if 'overrides' in imported_config:
                self._config_cache['overrides'] = imported_config['overrides']
                self._save_config_file(self.overrides_config_file, imported_config['overrides'])
            
            logger.info(f"Imported configuration from {input_file}")
            
        except Exception as e:
            logger.error(f"Failed to import configuration: {str(e)}")
            raise ConfigurationError(f"Import failed: {str(e)}")


# Global configuration manager instance
config_manager = ConfigManager()