"""
VisionSeal Configuration Management
Centralized, validated configuration with environment support
"""
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from pathlib import Path
import os

# Ensure .env file is loaded
from dotenv import load_dotenv
load_dotenv()


class DatabaseSettings(BaseSettings):
    """Database configuration"""
    url: str = Field(
        default="sqlite:///./data/visionseal.db",
        env="DATABASE_URL"
    )
    echo_queries: bool = Field(False, env="DATABASE_ECHO")
    pool_size: int = Field(10, env="DATABASE_POOL_SIZE")
    max_overflow: int = Field(20, env="DATABASE_MAX_OVERFLOW")
    
    class Config:
        env_prefix = "DATABASE_"


class RedisSettings(BaseSettings):
    """Redis configuration"""
    url: str = Field("redis://localhost:6379", env="REDIS_URL")
    max_connections: int = Field(10, env="REDIS_MAX_CONNECTIONS")
    
    class Config:
        env_prefix = "REDIS_"


class OpenAISettings(BaseSettings):
    """OpenAI configuration"""
    api_key: str = Field(..., env="OPENAI_API_KEY")
    model: str = Field("gpt-4-turbo", env="OPENAI_MODEL")
    max_tokens: int = Field(4000, env="OPENAI_MAX_TOKENS")
    temperature: float = Field(0.7, env="OPENAI_TEMPERATURE")
    
    class Config:
        env_prefix = "OPENAI_"


class WeaviateSettings(BaseSettings):
    """Weaviate vector database configuration"""
    url: str = Field("http://localhost:8090", env="WEAVIATE_URL")
    api_key: Optional[str] = Field(None, env="WEAVIATE_API_KEY")
    collection_name: str = Field("TenderChunks", env="WEAVIATE_COLLECTION_NAME")
    embedding_model: str = Field("text-embedding-3-large", env="WEAVIATE_EMBEDDING_MODEL")
    embedding_dimension: int = Field(3072, env="WEAVIATE_EMBEDDING_DIMENSION")
    
    class Config:
        env_prefix = "WEAVIATE_"


class AISettings(BaseSettings):
    """AI processing configuration"""
    chunk_size: int = Field(1500, env="AI_CHUNK_SIZE")
    chunk_overlap: int = Field(200, env="AI_CHUNK_OVERLAP")
    max_context_tokens: int = Field(3000, env="AI_MAX_CONTEXT_TOKENS")
    max_response_tokens: int = Field(4000, env="AI_MAX_RESPONSE_TOKENS")
    enable_ocr: bool = Field(False, env="AI_ENABLE_OCR")
    
    # RAG settings
    similarity_top_k: int = Field(10, env="AI_SIMILARITY_TOP_K")
    minimum_similarity_score: float = Field(0.3, env="AI_MIN_SIMILARITY_SCORE")
    
    # Response generation settings
    sections_config: List[str] = Field([
        "Introduction, Objectifs et Démarche",
        "Méthodologie et Livrables", 
        "Risques, Équipe et Conclusion"
    ], env="AI_SECTIONS_CONFIG")
    
    class Config:
        env_prefix = "AI_"


class AutomationSettings(BaseSettings):
    """Automation credentials and settings"""
    ungm_username: str = Field(..., env="UNGM_USERNAME")
    ungm_password: str = Field(..., env="UNGM_PASSWORD")
    tunipages_username: str = Field(..., env="TUNIPAGES_USERNAME")
    tunipages_password: str = Field(..., env="TUNIPAGES_PASSWORD")
    
    # Browser settings
    headless: bool = Field(True, env="BROWSER_HEADLESS")
    timeout: int = Field(30000, env="BROWSER_TIMEOUT")
    max_pages: int = Field(10, env="AUTOMATION_MAX_PAGES")
    request_delay: int = Field(2, env="AUTOMATION_REQUEST_DELAY")  # seconds between requests
    
    # Task Manager settings
    max_workers: int = Field(4, env="AUTOMATION_MAX_WORKERS")
    max_retries: int = Field(3, env="AUTOMATION_MAX_RETRIES")
    retry_delay: int = Field(300, env="AUTOMATION_RETRY_DELAY")  # 5 minutes default
    task_timeout: int = Field(3600, env="AUTOMATION_TASK_TIMEOUT")  # 1 hour default
    scheduler_interval: int = Field(30, env="AUTOMATION_SCHEDULER_INTERVAL")  # 30 seconds
    
    # Cleanup settings
    cleanup_completed_tasks_hours: int = Field(24, env="AUTOMATION_CLEANUP_HOURS")
    cleanup_failed_tasks_hours: int = Field(72, env="AUTOMATION_CLEANUP_FAILED_HOURS")
    
    # Performance settings
    max_concurrent_scrapers: int = Field(2, env="AUTOMATION_MAX_CONCURRENT_SCRAPERS")
    memory_threshold_mb: int = Field(1024, env="AUTOMATION_MEMORY_THRESHOLD_MB")  # 1GB
    
    # Monitoring settings
    enable_metrics: bool = Field(True, env="AUTOMATION_ENABLE_METRICS")
    metrics_retention_days: int = Field(30, env="AUTOMATION_METRICS_RETENTION_DAYS")
    alert_failure_threshold: float = Field(0.5, env="AUTOMATION_ALERT_FAILURE_THRESHOLD")  # 50%
    
    # Session settings
    session_persistence_enabled: bool = Field(True, env="AUTOMATION_SESSION_PERSISTENCE")
    session_retry_on_startup: bool = Field(True, env="AUTOMATION_SESSION_RETRY_ON_STARTUP")
    
    class Config:
        env_prefix = ""  # No prefix to read UNGM_USERNAME directly
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra fields


class SecuritySettings(BaseSettings):
    """Security configuration"""
    secret_key: str = Field(..., env="SECRET_KEY")
    allowed_origins: List[str] = Field(["http://localhost:3000"], env="ALLOWED_ORIGINS")
    max_file_size: int = Field(10 * 1024 * 1024, env="MAX_FILE_SIZE")  # 10MB
    allowed_file_types: List[str] = Field([".pdf", ".docx", ".pptx"], env="ALLOWED_FILE_TYPES")
    
    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @field_validator("allowed_file_types", mode="before")
    @classmethod
    def parse_file_types(cls, v):
        if isinstance(v, str):
            return [ft.strip() for ft in v.split(",")]
        return v
    
    class Config:
        env_prefix = "SECURITY_"


class APISettings(BaseSettings):
    """API configuration"""
    host: str = Field("0.0.0.0", env="API_HOST")
    port: int = Field(8080, env="API_PORT")
    workers: int = Field(1, env="API_WORKERS")
    reload: bool = Field(False, env="API_RELOAD")
    log_level: str = Field("INFO", env="API_LOG_LEVEL")
    
    class Config:
        env_prefix = "API_"


class Settings(BaseSettings):
    """Main application settings"""
    environment: str = Field("development", env="ENVIRONMENT")
    debug: bool = Field(False, env="DEBUG")
    project_name: str = "VisionSeal Complete"
    version: str = "2.0.0"
    
    # Sub-configurations (initialized in __init__)
    database: Optional[DatabaseSettings] = None
    redis: Optional[RedisSettings] = None
    openai: Optional[OpenAISettings] = None
    weaviate: Optional[WeaviateSettings] = None
    ai: Optional[AISettings] = None
    automation: Optional[AutomationSettings] = None
    security: Optional[SecuritySettings] = None
    api: Optional[APISettings] = None
    
    # Paths
    base_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent.parent)
    data_dir: Path = Field(default_factory=lambda: Path("data"))
    logs_dir: Path = Field(default_factory=lambda: Path("logs"))
    uploads_dir: Path = Field(default_factory=lambda: Path("uploads"))
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Initialize sub-configurations with proper error handling
        try:
            self.database = DatabaseSettings()
        except Exception:
            # Fallback for demo
            self.database = DatabaseSettings(url="sqlite:///./visionseal_demo.db")
        
        try:
            self.redis = RedisSettings()
        except Exception:
            self.redis = RedisSettings()
        
        try:
            self.openai = OpenAISettings()
        except Exception as e:
            # Only use fallback if API key is truly not available
            import os
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.openai = OpenAISettings(api_key=api_key)
            else:
                self.openai = OpenAISettings(api_key="demo-key-replace-with-real-key")
        
        try:
            self.weaviate = WeaviateSettings()
        except Exception:
            self.weaviate = WeaviateSettings()
        
        try:
            self.ai = AISettings()
        except Exception:
            self.ai = AISettings()
        
        try:
            self.automation = AutomationSettings()
        except Exception:
            # Fallback for demo
            self.automation = AutomationSettings(
                ungm_username="demo-username",
                ungm_password="demo-password",
                tunipages_username="demo-username",
                tunipages_password="demo-password"
            )
        
        try:
            self.security = SecuritySettings()
        except Exception:
            # Fallback for demo
            self.security = SecuritySettings(secret_key="demo-secret-key-for-testing-only")
        
        try:
            self.api = APISettings()
        except Exception:
            self.api = APISettings()
        
        # Create directories
        self.create_directories()
    
    def create_directories(self):
        """Create necessary directories"""
        directories = [
            self.data_dir,
            self.logs_dir,
            self.uploads_dir,
            self.uploads_dir / "temp",
            self.data_dir / "extractions",
            self.data_dir / "ai_responses"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v):
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"Environment must be one of {allowed}")
        return v
    
    def get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from environment
        arbitrary_types_allowed = True  # Allow complex types


# Global settings instance
settings = Settings()