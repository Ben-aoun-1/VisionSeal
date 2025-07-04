"""
Security Configuration for VisionSeal
Centralized security settings and policies
"""
import os
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class SecurityConfig:
    """Centralized security configuration"""
    
    # Authentication & Authorization
    JWT_SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_SPECIAL: bool = True
    SESSION_TIMEOUT_MINUTES: int = 30
    
    # CORS Settings
    ALLOWED_ORIGINS: List[str] = None
    ALLOWED_METHODS: List[str] = None
    ALLOWED_HEADERS: List[str] = None
    ALLOW_CREDENTIALS: bool = False
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_MINUTES: int = 15
    RATE_LIMIT_BURST: int = 20
    
    # File Upload Security
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: List[str] = None
    UPLOAD_PATH: str = "./uploads"
    SCAN_UPLOADS: bool = True
    
    # Input Validation
    MAX_STRING_LENGTH: int = 1000
    MAX_JSON_SIZE: int = 1024 * 1024  # 1MB
    SANITIZE_HTML: bool = True
    
    # Browser Automation Security
    BROWSER_SANDBOX: bool = True
    BROWSER_WEB_SECURITY: bool = True
    BROWSER_TIMEOUT: int = 30000
    
    # Logging Security
    LOG_SENSITIVE_DATA: bool = False
    LOG_LEVEL: str = "INFO"
    LOG_ROTATION: bool = True
    
    # Database Security
    DB_SSL_REQUIRED: bool = True
    DB_CONNECTION_TIMEOUT: int = 30
    DB_QUERY_TIMEOUT: int = 60
    
    # API Security Headers
    SECURITY_HEADERS: Dict[str, str] = None
    
    def __post_init__(self):
        """Initialize default values"""
        if not self.JWT_SECRET_KEY:
            raise ValueError("SECRET_KEY environment variable is required")
            
        if self.ALLOWED_ORIGINS is None:
            self.ALLOWED_ORIGINS = [
                "http://localhost:3000",
                "http://localhost:8080",
                "http://127.0.0.1:8080"
            ]
            
        if self.ALLOWED_METHODS is None:
            self.ALLOWED_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
            
        if self.ALLOWED_HEADERS is None:
            self.ALLOWED_HEADERS = [
                "Authorization",
                "Content-Type",
                "X-Requested-With"
            ]
            
        if self.ALLOWED_FILE_TYPES is None:
            self.ALLOWED_FILE_TYPES = [".pdf", ".docx", ".xlsx", ".pptx"]
            
        if self.SECURITY_HEADERS is None:
            self.SECURITY_HEADERS = {
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
                "X-XSS-Protection": "1; mode=block",
                "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
                "Content-Security-Policy": (
                    "default-src 'self'; "
                    "script-src 'self' 'unsafe-inline' https://unpkg.com; "
                    "style-src 'self' 'unsafe-inline'; "
                    "img-src 'self' data: https:; "
                    "connect-src 'self' https://*.supabase.co; "
                    "frame-ancestors 'none'"
                ),
                "Referrer-Policy": "strict-origin-when-cross-origin",
                "Permissions-Policy": (
                    "geolocation=(), microphone=(), camera=(), "
                    "payment=(), usb=(), bluetooth=()"
                )
            }
    
    def get_browser_args(self) -> List[str]:
        """Get secure browser arguments"""
        args = [
            '--disable-blink-features=AutomationControlled',
            '--disable-features=VizDisplayCompositor',
            '--disable-background-timer-throttling',
            '--disable-renderer-backgrounding',
            '--disable-backgrounding-occluded-windows'
        ]
        
        # Only add security-disabling flags if explicitly allowed
        if not self.BROWSER_SANDBOX:
            args.append('--no-sandbox')
            
        if not self.BROWSER_WEB_SECURITY:
            args.append('--disable-web-security')
            
        return args
    
    def validate_file_upload(self, filename: str, content_type: str, size: int) -> bool:
        """Validate file upload security"""
        import os
        
        # Check file size
        if size > self.MAX_FILE_SIZE:
            return False
            
        # Check file extension
        _, ext = os.path.splitext(filename.lower())
        if ext not in self.ALLOWED_FILE_TYPES:
            return False
            
        # Additional MIME type validation
        allowed_mime_types = {
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
        }
        
        expected_mime = allowed_mime_types.get(ext)
        if expected_mime and content_type != expected_mime:
            return False
            
        return True
    
    def sanitize_string(self, text: str) -> str:
        """Sanitize string input"""
        if not text:
            return ""
            
        # Limit length
        text = text[:self.MAX_STRING_LENGTH]
        
        if self.SANITIZE_HTML:
            # Basic HTML sanitization
            import html
            text = html.escape(text)
            
        return text.strip()

# Global security configuration instance
security_config = SecurityConfig()

def get_security_config() -> SecurityConfig:
    """Get the global security configuration"""
    return security_config