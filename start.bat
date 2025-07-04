@echo off
title VisionSeal Complete - Refactored Edition
cls

echo ================================================================
echo 🎯 VisionSeal Complete - Secure Refactored Version
echo ================================================================
echo Version: 2.0.0
echo Environment: Production-Ready with Security Features
echo ================================================================
echo.

echo 🔧 Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found! Please install Python 3.9+ first.
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo ✅ Python found

echo.
echo 🔧 Setting up virtual environment...
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ❌ Failed to create virtual environment
        pause
        exit /b 1
    )
)

echo 📦 Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ Failed to activate virtual environment
    pause
    exit /b 1
)

echo.
echo 📦 Installing dependencies...
pip install fastapi uvicorn pydantic pydantic-settings python-jose passlib python-multipart python-dotenv python-magic PyJWT --quiet
if errorlevel 1 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)
echo ✅ Dependencies installed

echo.
echo 🔍 Checking configuration...
if not exist ".env" (
    echo ❌ .env file not found! Please ensure .env file exists.
    pause
    exit /b 1
)
echo ✅ Configuration found

echo.
echo 🔧 Setting up Python path...
set PYTHONPATH=%CD%
echo ✅ Python path configured

echo.
echo 🚀 Starting VisionSeal Complete (Secure Edition)...
echo.
echo 📍 Server will be available at:
echo    • Main Interface: http://localhost:8080
echo    • API Documentation: http://localhost:8080/docs  
echo    • Health Check: http://localhost:8080/health
echo.
echo 🛡️ Security Features Enabled:
echo    • Input validation and sanitization
echo    • Rate limiting and request throttling  
echo    • Secure file upload handling
echo    • Structured logging with correlation IDs
echo    • CORS protection with allowed origins
echo.
echo 💡 Press Ctrl+C to stop the server
echo ================================================================
echo.

REM Try different approaches to start the server
echo Attempting to start server...

REM Method 1: Direct Python execution
python -c "import sys; sys.path.insert(0, '.'); from src.main import app; import uvicorn; uvicorn.run(app, host='0.0.0.0', port=8080, reload=True)"

REM If that fails, try Method 2: Using uvicorn with PYTHONPATH
if errorlevel 1 (
    echo Trying alternative startup method...
    python -m uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload
)

echo.
echo 🛑 VisionSeal server stopped.
pause