"""
Security module unit tests
Tests for critical security validations
"""
import pytest
from fastapi import HTTPException, UploadFile
from io import BytesIO
from pathlib import Path

from src.core.security.validators import (
    FileValidator,
    PathValidator,
    InputValidator,
    RateLimiter
)


class TestFileValidator:
    """Test file validation and sanitization"""
    
    def test_sanitize_filename_removes_dangerous_chars(self):
        """Test filename sanitization removes dangerous characters"""
        dangerous_filename = "../../../etc/passwd"
        result = FileValidator.sanitize_filename(dangerous_filename)
        assert result == "etcpasswd"
    
    def test_sanitize_filename_removes_hidden_files(self):
        """Test hidden file indicators are removed"""
        hidden_filename = ".hidden_file.txt"
        result = FileValidator.sanitize_filename(hidden_filename)
        assert result is None  # Hidden files rejected
    
    def test_sanitize_filename_limits_length(self):
        """Test filename length is limited"""
        long_filename = "a" * 300 + ".txt"
        result = FileValidator.sanitize_filename(long_filename)
        assert len(result) <= 255
        assert result.endswith(".txt")
    
    def test_validate_file_upload_rejects_large_files(self):
        """Test file size validation"""
        # Mock upload file with large size
        mock_file = UploadFile(
            filename="test.pdf",
            file=BytesIO(b"test content")
        )
        mock_file.size = 50 * 1024 * 1024  # 50MB
        
        with pytest.raises(HTTPException) as exc_info:
            FileValidator.validate_file_upload(mock_file)
        
        assert exc_info.value.status_code == 413
    
    def test_validate_file_upload_rejects_invalid_extensions(self):
        """Test file extension validation"""
        mock_file = UploadFile(
            filename="malicious.exe",
            file=BytesIO(b"test content")
        )
        
        with pytest.raises(HTTPException) as exc_info:
            FileValidator.validate_file_upload(mock_file)
        
        assert exc_info.value.status_code == 400
        assert "File type not allowed" in str(exc_info.value.detail)


class TestPathValidator:
    """Test path validation and sanitization"""
    
    def test_validate_file_path_prevents_traversal(self):
        """Test path traversal prevention"""
        base_dir = Path("/safe/directory")
        dangerous_path = "../../../etc/passwd"
        
        with pytest.raises(HTTPException) as exc_info:
            PathValidator.validate_file_path(dangerous_path, base_dir)
        
        assert exc_info.value.status_code == 400
        assert "Access denied" in str(exc_info.value.detail)
    
    def test_validate_file_path_allows_safe_paths(self):
        """Test safe paths are allowed"""
        base_dir = Path("/safe/directory")
        safe_path = "subdirectory/file.txt"
        
        result = PathValidator.validate_file_path(safe_path, base_dir)
        assert str(result).startswith(str(base_dir))
    
    def test_sanitize_path_removes_traversal_attempts(self):
        """Test path sanitization"""
        dangerous_path = "../../../file.txt"
        result = PathValidator.sanitize_path(dangerous_path)
        assert not result.startswith("../")


class TestInputValidator:
    """Test input validation and sanitization"""
    
    def test_validate_command_input_rejects_unlisted_commands(self):
        """Test command validation rejects unlisted commands"""
        allowed_commands = ["start", "stop", "status"]
        dangerous_command = "rm -rf /"
        
        with pytest.raises(HTTPException) as exc_info:
            InputValidator.validate_command_input(dangerous_command, allowed_commands)
        
        assert exc_info.value.status_code == 400
        assert "Invalid command" in str(exc_info.value.detail)
    
    def test_validate_command_input_allows_listed_commands(self):
        """Test command validation allows listed commands"""
        allowed_commands = ["start", "stop", "status"]
        valid_command = "start"
        
        result = InputValidator.validate_command_input(valid_command, allowed_commands)
        assert result == valid_command
    
    def test_sanitize_user_input_removes_dangerous_chars(self):
        """Test user input sanitization"""
        dangerous_input = "<script>alert('xss')</script>"
        result = InputValidator.sanitize_user_input(dangerous_input)
        assert "<script>" not in result
        assert "alert('xss')" not in result
    
    def test_validate_source_parameter_rejects_invalid_sources(self):
        """Test source parameter validation"""
        invalid_source = "malicious_source"
        
        with pytest.raises(HTTPException) as exc_info:
            InputValidator.validate_source_parameter(invalid_source)
        
        assert exc_info.value.status_code == 400
    
    def test_validate_source_parameter_allows_valid_sources(self):
        """Test source parameter validation allows valid sources"""
        valid_sources = ["ungm", "tunipages", "both"]
        
        for source in valid_sources:
            result = InputValidator.validate_source_parameter(source)
            assert result == source


class TestRateLimiter:
    """Test rate limiting functionality"""
    
    def test_rate_limiter_allows_within_limits(self):
        """Test rate limiter allows requests within limits"""
        limiter = RateLimiter()
        
        # Should allow first request
        assert limiter.is_allowed("test_key", max_requests=5, window_seconds=60)
        
        # Should allow subsequent requests within limit
        for _ in range(4):
            assert limiter.is_allowed("test_key", max_requests=5, window_seconds=60)
    
    def test_rate_limiter_blocks_over_limits(self):
        """Test rate limiter blocks requests over limits"""
        limiter = RateLimiter()
        
        # Use up the limit
        for _ in range(5):
            limiter.is_allowed("test_key", max_requests=5, window_seconds=60)
        
        # Next request should be blocked
        assert not limiter.is_allowed("test_key", max_requests=5, window_seconds=60)
    
    def test_rate_limiter_resets_after_window(self):
        """Test rate limiter resets after time window"""
        limiter = RateLimiter()
        
        # Use up the limit
        for _ in range(5):
            limiter.is_allowed("test_key", max_requests=5, window_seconds=1)
        
        # Should be blocked
        assert not limiter.is_allowed("test_key", max_requests=5, window_seconds=1)
        
        # Wait for window to reset (in real test, would mock time)
        import time
        time.sleep(1.1)
        
        # Should be allowed again
        assert limiter.is_allowed("test_key", max_requests=5, window_seconds=1)