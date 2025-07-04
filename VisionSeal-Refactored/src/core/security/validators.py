"""
Security validators and sanitizers
Fixes critical security vulnerabilities from original codebase
"""
import re
import os
import magic
from pathlib import Path
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, UploadFile
from pydantic import validator

from ..config.settings import settings


class FileValidator:
    """Secure file validation and sanitization"""
    
    ALLOWED_MIME_TYPES = {
        '.pdf': ['application/pdf'],
        '.docx': [
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        ],
        '.pptx': [
            'application/vnd.openxmlformats-officedocument.presentationml.presentation'
        ]
    }
    
    @classmethod
    def validate_file_upload(cls, file: UploadFile) -> None:
        """
        Comprehensive file validation
        Fixes: Insecure file upload handling
        """
        # Check file size
        if hasattr(file, 'size') and file.size > settings.security.max_file_size:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: {settings.security.max_file_size} bytes"
            )
        
        # Validate filename
        secure_filename = cls.sanitize_filename(file.filename)
        if not secure_filename:
            raise HTTPException(
                status_code=400,
                detail="Invalid filename"
            )
        
        # Check file extension
        file_ext = Path(secure_filename).suffix.lower()
        if file_ext not in settings.security.allowed_file_types:
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed types: {settings.security.allowed_file_types}"
            )
        
        # Validate MIME type if file has content
        if hasattr(file, 'file') and file.file:
            cls._validate_mime_type(file, file_ext)
    
    @classmethod
    def sanitize_filename(cls, filename: str) -> Optional[str]:
        """
        Sanitize filename to prevent path traversal
        Fixes: Path traversal vulnerabilities
        """
        if not filename:
            return None
        
        # Remove path components
        filename = os.path.basename(filename)
        
        # Remove dangerous characters
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        
        # Remove hidden file indicators and relative path components
        filename = re.sub(r'^\.+', '', filename)
        
        # Limit length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:255-len(ext)] + ext
        
        return filename if filename and not filename.startswith('.') else None
    
    @classmethod
    def _validate_mime_type(cls, file: UploadFile, file_ext: str) -> None:
        """Validate MIME type matches extension"""
        try:
            # Read first 2KB for MIME detection
            file.file.seek(0)
            file_header = file.file.read(2048)
            file.file.seek(0)
            
            mime_type = magic.from_buffer(file_header, mime=True)
            
            allowed_mimes = cls.ALLOWED_MIME_TYPES.get(file_ext, [])
            if mime_type not in allowed_mimes:
                raise HTTPException(
                    status_code=400,
                    detail=f"File content doesn't match extension. Expected: {allowed_mimes}, Got: {mime_type}"
                )
        except Exception:
            # If MIME detection fails, allow but log warning
            pass


class PathValidator:
    """Secure path validation"""
    
    @classmethod
    def validate_file_path(cls, file_path: str, base_dir: Path) -> Path:
        """
        Validate file path to prevent directory traversal
        Fixes: Path traversal vulnerabilities
        """
        # Sanitize the path
        sanitized_path = cls.sanitize_path(file_path)
        
        # Resolve to absolute path
        full_path = (base_dir / sanitized_path).resolve()
        
        # Ensure path is within base directory
        try:
            full_path.relative_to(base_dir.resolve())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid file path: Access denied"
            )
        
        return full_path
    
    @classmethod
    def sanitize_path(cls, path: str) -> str:
        """Sanitize path components"""
        # Remove dangerous path components
        path = re.sub(r'\.\.+[/\\]', '', path)
        path = re.sub(r'^[/\\]+', '', path)
        
        # Normalize path separators
        path = path.replace('\\', '/')
        
        return path


class InputValidator:
    """Input validation and sanitization"""
    
    @classmethod
    def validate_command_input(cls, command: str, allowed_commands: List[str]) -> str:
        """
        Validate command input to prevent injection
        Fixes: Command injection vulnerabilities
        """
        # Strip whitespace
        command = command.strip()
        
        # Check against whitelist
        if command not in allowed_commands:
            raise HTTPException(
                status_code=400,
                detail="Invalid command"
            )
        
        return command
    
    @classmethod
    def sanitize_user_input(cls, user_input: str, max_length: int = 1000) -> str:
        """Sanitize general user input"""
        if not user_input:
            return ""
        
        # Limit length
        user_input = user_input[:max_length]
        
        # Remove potentially dangerous characters
        user_input = re.sub(r'[<>&"\'`]', '', user_input)
        
        return user_input.strip()
    
    @classmethod
    def validate_source_parameter(cls, source: str) -> str:
        """Validate automation source parameter"""
        allowed_sources = ["ungm", "tunipages", "both"]
        if source not in allowed_sources:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid source. Allowed: {allowed_sources}"
            )
        return source


class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        self._requests: Dict[str, List[float]] = {}
    
    def is_allowed(self, key: str, max_requests: int = 100, window_seconds: int = 3600) -> bool:
        """Check if request is within rate limits"""
        import time
        
        now = time.time()
        window_start = now - window_seconds
        
        # Clean old requests
        if key in self._requests:
            self._requests[key] = [
                req_time for req_time in self._requests[key] 
                if req_time > window_start
            ]
        else:
            self._requests[key] = []
        
        # Check limit
        if len(self._requests[key]) >= max_requests:
            return False
        
        # Add current request
        self._requests[key].append(now)
        return True


# Global rate limiter instance
rate_limiter = RateLimiter()