"""
VisionSeal Configuration Management
Centralized, validated configuration with environment support
"""
from typing import List, Optional
from pydantic import BaseSettings, validator, Field
from pathlib import Path
import os


class DatabaseSettings(BaseSettings):
    """Database configuration"""
    url: str = Field(..., env="DATABASE_URL")
    echo: bool = Field(False, env="DATABASE_ECHO")
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
    
    class Config:
        env_prefix = "WEAVIATE_"


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
    
    class Config:
        env_prefix = "AUTOMATION_"


class SecuritySettings(BaseSettings):
    """Security configuration"""
    secret_key: str = Field(..., env="SECRET_KEY")
    allowed_origins: List[str] = Field(["http://localhost:3000"], env="ALLOWED_ORIGINS")
    max_file_size: int = Field(10 * 1024 * 1024, env="MAX_FILE_SIZE")  # 10MB
    allowed_file_types: List[str] = Field([".pdf", ".docx", ".pptx"], env="ALLOWED_FILE_TYPES")
    
    @validator("allowed_origins", pre=True)
    def parse_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("allowed_file_types", pre=True)
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
    
    # Sub-configurations
    database: DatabaseSettings
    redis: RedisSettings
    openai: OpenAISettings
    weaviate: WeaviateSettings
    automation: AutomationSettings
    security: SecuritySettings
    api: APISettings
    
    # Paths
    base_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent.parent)
    data_dir: Path = Field(default_factory=lambda: Path("data"))
    logs_dir: Path = Field(default_factory=lambda: Path("logs"))
    uploads_dir: Path = Field(default_factory=lambda: Path("uploads"))
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialize sub-configurations
        self.database = DatabaseSettings()
        self.redis = RedisSettings()
        self.openai = OpenAISettings()
        self.weaviate = WeaviateSettings()
        self.automation = AutomationSettings()
        self.security = SecuritySettings()
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
    
    @validator("environment")
    def validate_environment(cls, v):
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"Environment must be one of {allowed}")
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()