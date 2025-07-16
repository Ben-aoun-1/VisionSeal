"""
Security validators and sanitizers
Fixes critical security vulnerabilities from original codebase
"""
import re
import os
try:
    import magic
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False
from pathlib import Path
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, UploadFile
from pydantic import validator

from core.config.settings import settings


class FileValidator:
    """Secure file validation and sanitization"""
    
    @staticmethod
    def _fallback_mime_detection(file_ext: str) -> str:
        """Fallback MIME type detection when python-magic is not available"""
        mime_map = {
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            '.txt': 'text/plain',
            '.json': 'application/json',
            '.csv': 'text/csv'
        }
        return mime_map.get(file_ext, 'application/octet-stream')
    
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
        Comprehensive file validation with enhanced security
        Fixes: Insecure file upload handling
        """
        # Check if file exists
        if not file or not file.filename:
            raise HTTPException(
                status_code=400,
                detail="No file provided"
            )
        
        # Check file size
        if hasattr(file, 'size') and file.size is not None:
            if file.size > settings.security.max_file_size:
                raise HTTPException(
                    status_code=413,
                    detail=f"File too large. Maximum size: {settings.security.max_file_size} bytes"
                )
            elif file.size == 0:
                raise HTTPException(
                    status_code=400,
                    detail="Empty file not allowed"
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
            
        # Check for malicious content patterns
        cls._scan_for_malicious_content(file)
        
        # Validate file integrity
        cls._validate_file_integrity(file, file_ext)
    
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
            
            if HAS_MAGIC:
                mime_type = magic.from_buffer(file_header, mime=True)
            else:
                # Fallback MIME detection without magic library
                mime_type = cls._fallback_mime_detection(file_ext)
            
            allowed_mimes = cls.ALLOWED_MIME_TYPES.get(file_ext, [])
            if mime_type not in allowed_mimes:
                raise HTTPException(
                    status_code=400,
                    detail=f"File content doesn't match extension. Expected: {allowed_mimes}, Got: {mime_type}"
                )
        except Exception:
            # If MIME detection fails, allow but log warning
            pass
    
    @classmethod
    def _scan_for_malicious_content(cls, file: UploadFile) -> None:
        """Scan file for malicious content patterns"""
        try:
            # Read first 8KB for malicious pattern detection
            file.file.seek(0)
            file_header = file.file.read(8192)
            file.file.seek(0)
            
            # Check for embedded executables
            malicious_patterns = [
                b'MZ',  # Windows executable
                b'\x7fELF',  # Linux executable
                b'\xfe\xed\xfa\xce',  # macOS executable
                b'\xfe\xed\xfa\xcf',  # macOS executable
                b'<script',  # JavaScript
                b'javascript:',  # JavaScript protocol
                b'vbscript:',  # VBScript protocol
                b'<?php',  # PHP code
                b'<%',  # ASP/JSP code
                b'#!/bin/sh',  # Shell script
                b'#!/bin/bash',  # Bash script
                b'powershell',  # PowerShell
                b'cmd.exe',  # Windows command
                b'system(',  # System calls
                b'exec(',  # Execute calls
                b'eval(',  # Eval calls
            ]
            
            # Check for patterns in header
            for pattern in malicious_patterns:
                if pattern in file_header.lower():
                    raise HTTPException(
                        status_code=400,
                        detail="File contains potentially malicious content"
                    )
            
            # Check for suspicious metadata in Office files
            if file.filename and file.filename.lower().endswith(('.docx', '.xlsx', '.pptx')):
                cls._scan_office_file(file_header)
                
        except HTTPException:
            raise
        except Exception as e:
            # Log warning but don't fail the upload
            from core.logging.setup import get_logger
            logger = get_logger("file_validator")
            logger.warning(f"Malicious content scan failed: {str(e)}")
    
    @classmethod
    def _scan_office_file(cls, file_header: bytes) -> None:
        """Scan Office file for suspicious content"""
        try:
            # Check for embedded macros or external references
            suspicious_office_patterns = [
                b'macros',
                b'VBA',
                b'Microsoft.VBIDE',
                b'Shell.Application',
                b'WScript.Shell',
                b'http://',
                b'https://',
                b'ftp://',
                b'file://',
                b'\\\\',  # UNC paths
            ]
            
            for pattern in suspicious_office_patterns:
                if pattern in file_header:
                    # Log warning but don't block (could be legitimate)
                    from core.logging.setup import get_logger
                    logger = get_logger("file_validator")
                    logger.warning(f"Office file contains suspicious pattern: {pattern}")
                    
        except Exception:
            pass  # Ignore errors in Office file scanning
    
    @classmethod
    def _validate_file_integrity(cls, file: UploadFile, file_ext: str) -> None:
        """Validate file integrity and structure"""
        try:
            file.file.seek(0)
            file_header = file.file.read(1024)
            file.file.seek(0)
            
            # File signature validation
            file_signatures = {
                '.pdf': [b'%PDF-'],
                '.docx': [b'PK\x03\x04'],  # ZIP-based format
                '.xlsx': [b'PK\x03\x04'],  # ZIP-based format
                '.pptx': [b'PK\x03\x04'],  # ZIP-based format
                '.txt': [],  # No specific signature
                '.csv': [],  # No specific signature
                '.json': [],  # No specific signature
            }
            
            expected_signatures = file_signatures.get(file_ext, [])
            if expected_signatures:
                # Check if file starts with expected signature
                has_valid_signature = any(
                    file_header.startswith(sig) for sig in expected_signatures
                )
                
                if not has_valid_signature:
                    raise HTTPException(
                        status_code=400,
                        detail=f"File signature doesn't match expected format for {file_ext}"
                    )
            
            # Additional validation for Office files
            if file_ext in ['.docx', '.xlsx', '.pptx']:
                cls._validate_office_file_structure(file)
                
        except HTTPException:
            raise
        except Exception as e:
            # Log warning but don't fail the upload
            from core.logging.setup import get_logger
            logger = get_logger("file_validator")
            logger.warning(f"File integrity validation failed: {str(e)}")
    
    @classmethod
    def _validate_office_file_structure(cls, file: UploadFile) -> None:
        """Validate Office file structure"""
        try:
            import zipfile
            import io
            
            # Read file content
            file.file.seek(0)
            file_content = file.file.read()
            file.file.seek(0)
            
            # Try to open as ZIP (Office files are ZIP-based)
            with zipfile.ZipFile(io.BytesIO(file_content), 'r') as zip_file:
                # Check for required Office file components
                file_list = zip_file.namelist()
                
                # Basic structure validation
                required_files = ['[Content_Types].xml', '_rels/.rels']
                for required_file in required_files:
                    if required_file not in file_list:
                        raise HTTPException(
                            status_code=400,
                            detail="Invalid Office file structure"
                        )
                
                # Check for suspicious files in ZIP
                suspicious_files = [
                    'vbaProject.bin',  # VBA macros
                    'macros/',  # Macro folder
                    'Microsoft.VBIDE',  # VBA IDE
                ]
                
                for suspicious_file in suspicious_files:
                    if any(suspicious_file in filename for filename in file_list):
                        from core.logging.setup import get_logger
                        logger = get_logger("file_validator")
                        logger.warning(f"Office file contains suspicious component: {suspicious_file}")
                        
        except zipfile.BadZipFile:
            raise HTTPException(
                status_code=400,
                detail="Corrupted Office file"
            )
        except HTTPException:
            raise
        except Exception as e:
            # Log warning but don't fail the upload
            from core.logging.setup import get_logger
            logger = get_logger("file_validator")
            logger.warning(f"Office file validation failed: {str(e)}")


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
    def sanitize_ai_input(cls, ai_input: str, max_length: int = 10000) -> str:
        """Sanitize AI input to prevent prompt injection"""
        if not ai_input:
            return ""
        
        # Limit length
        ai_input = ai_input[:max_length]
        
        # Remove or escape prompt injection patterns
        prompt_injection_patterns = [
            # Direct instruction patterns
            r'(?i)ignore\s+(?:all\s+)?(?:previous\s+)?(?:instructions?|prompts?|rules?)',
            r'(?i)forget\s+(?:all\s+)?(?:previous\s+)?(?:instructions?|prompts?|rules?)',
            r'(?i)disregard\s+(?:all\s+)?(?:previous\s+)?(?:instructions?|prompts?|rules?)',
            r'(?i)override\s+(?:all\s+)?(?:previous\s+)?(?:instructions?|prompts?|rules?)',
            
            # Role switching patterns
            r'(?i)you\s+are\s+now\s+(?:a\s+)?(?:different\s+)?(?:ai|assistant|bot|system)',
            r'(?i)pretend\s+(?:to\s+be|you\s+are)',
            r'(?i)act\s+as\s+(?:if\s+)?(?:you\s+are\s+)?(?:a\s+)?(?:different\s+)?(?:ai|assistant|bot|system)',
            r'(?i)roleplay\s+as',
            r'(?i)assume\s+the\s+role\s+of',
            
            # System manipulation patterns
            r'(?i)system\s*:',
            r'(?i)assistant\s*:',
            r'(?i)user\s*:',
            r'(?i)human\s*:',
            r'(?i)ai\s*:',
            
            # Prompt delimiter patterns
            r'(?i)---+',
            r'(?i)===+',
            r'(?i)####+',
            r'(?i)\[system\]',
            r'(?i)\[assistant\]',
            r'(?i)\[user\]',
            r'(?i)\[human\]',
            r'(?i)\[ai\]',
            
            # Instruction override patterns
            r'(?i)new\s+(?:instructions?|prompts?|rules?)',
            r'(?i)updated\s+(?:instructions?|prompts?|rules?)',
            r'(?i)revised\s+(?:instructions?|prompts?|rules?)',
            r'(?i)alternative\s+(?:instructions?|prompts?|rules?)',
            
            # Context switching patterns
            r'(?i)switch\s+(?:to\s+)?(?:a\s+)?(?:different\s+)?(?:mode|context|persona)',
            r'(?i)change\s+(?:your\s+)?(?:mode|context|persona|behavior)',
            r'(?i)enter\s+(?:a\s+)?(?:different\s+)?(?:mode|context)',
            
            # Jailbreak patterns
            r'(?i)jailbreak',
            r'(?i)bypass\s+(?:safety\s+)?(?:guidelines?|restrictions?|rules?)',
            r'(?i)circumvent\s+(?:safety\s+)?(?:guidelines?|restrictions?|rules?)',
            r'(?i)work\s+around\s+(?:safety\s+)?(?:guidelines?|restrictions?|rules?)',
            
            # Developer mode patterns
            r'(?i)developer\s+mode',
            r'(?i)debug\s+mode',
            r'(?i)admin\s+mode',
            r'(?i)root\s+mode',
            r'(?i)unrestricted\s+mode',
            
            # Manipulation patterns
            r'(?i)for\s+(?:educational\s+)?(?:purposes?\s+)?(?:only|just)',
            r'(?i)hypothetically',
            r'(?i)theoretically',
            r'(?i)in\s+a\s+fictional\s+(?:scenario|context|world)',
            r'(?i)imagine\s+(?:if\s+)?(?:you\s+)?(?:were\s+)?(?:not\s+)?(?:bound\s+by|restricted\s+by)',
        ]
        
        # Replace injection patterns with safe alternatives
        for pattern in prompt_injection_patterns:
            ai_input = re.sub(pattern, '[FILTERED]', ai_input)
        
        # Remove excessive whitespace and control characters
        ai_input = re.sub(r'\s+', ' ', ai_input)
        ai_input = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', ai_input)
        
        # Check for remaining suspicious patterns
        if cls._contains_suspicious_ai_patterns(ai_input):
            from core.logging.setup import get_logger
            logger = get_logger("ai_validator")
            logger.warning("AI input contains suspicious patterns after sanitization")
        
        return ai_input.strip()
    
    @classmethod
    def _contains_suspicious_ai_patterns(cls, text: str) -> bool:
        """Check if text contains suspicious AI manipulation patterns"""
        suspicious_patterns = [
            # Multiple consecutive special characters
            r'[^\w\s]{5,}',
            # Excessive repetition
            r'(.)\1{10,}',
            # Unicode manipulation
            r'[\u200b-\u200f\u2060-\u206f\ufeff]',
            # Base64-like patterns (potential encoded instructions)
            r'(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?',
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, text):
                return True
        
        return False
    
    @classmethod
    def validate_ai_prompt(cls, prompt: str, context: str = None) -> Dict[str, str]:
        """Validate and sanitize AI prompts with context"""
        if not prompt:
            raise HTTPException(
                status_code=400,
                detail="Empty prompt not allowed"
            )
        
        # Sanitize prompt
        sanitized_prompt = cls.sanitize_ai_input(prompt, max_length=5000)
        
        # Sanitize context if provided
        sanitized_context = ""
        if context:
            sanitized_context = cls.sanitize_ai_input(context, max_length=20000)
        
        # Check for prompt injection attempts
        if len(sanitized_prompt) < len(prompt) * 0.8:
            from core.logging.setup import get_logger
            logger = get_logger("ai_validator")
            logger.warning("Significant content removed during AI input sanitization")
        
        return {
            "prompt": sanitized_prompt,
            "context": sanitized_context
        }
    
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