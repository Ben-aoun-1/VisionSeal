"""
Pytest configuration and fixtures for VisionSeal tests
"""
import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, AsyncMock
from fastapi.testclient import TestClient
from fastapi import UploadFile
import io

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

@pytest.fixture
def mock_settings():
    """Mock application settings"""
    from core.config.settings import Settings
    
    settings = Settings()
    settings.security.max_file_size = 10 * 1024 * 1024  # 10MB
    settings.security.allowed_file_types = [".pdf", ".docx", ".pptx", ".txt"]
    settings.uploads_dir = Path("/tmp/test_uploads")
    settings.data_dir = Path("/tmp/test_data")
    
    # Ensure directories exist
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    
    return settings

@pytest.fixture
def mock_file_upload():
    """Create mock file upload objects for testing"""
    def create_mock_file(filename: str, content: bytes, content_type: str = "application/pdf"):
        file_obj = io.BytesIO(content)
        upload_file = UploadFile(
            filename=filename,
            file=file_obj,
            content_type=content_type,
            size=len(content)
        )
        return upload_file
    
    return create_mock_file

@pytest.fixture
def pdf_file_content():
    """Sample PDF file content for testing"""
    return b'%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n'

@pytest.fixture
def malicious_file_content():
    """Malicious file content patterns for testing"""
    return {
        'executable': b'MZ\x90\x00\x03\x00\x00\x00',  # Windows executable header
        'script': b'<script>alert("xss")</script>',
        'php': b'<?php system($_GET["cmd"]); ?>',
        'shell': b'#!/bin/bash\nrm -rf /',
    }

@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for testing"""
    client = Mock()
    client.auth = Mock()
    client.table = Mock()
    return client

@pytest.fixture
def mock_user():
    """Mock user for testing"""
    return {
        "user_id": "test-user-123",
        "email": "test@example.com",
        "email_verified": True,
        "created_at": "2024-01-01T00:00:00Z",
        "profile": {
            "first_name": "Test",
            "last_name": "User",
            "company": "Test Company"
        }
    }

@pytest.fixture
def mock_jwt_token():
    """Mock JWT token for testing"""
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0LXVzZXItMTIzIiwiZW1haWwiOiJ0ZXN0QGV4YW1wbGUuY29tIiwiaWF0IjoxNjQwOTk1MjAwLCJleHAiOjE2NDA5OTg4MDB9.test-signature"

@pytest.fixture
def test_client():
    """Create test client for API testing"""
    # Import after path setup
    from main import app
    return TestClient(app)

@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing"""
    client = Mock()
    client.chat = Mock()
    client.chat.completions = Mock()
    client.chat.completions.create = Mock()
    return client