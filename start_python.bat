@echo off
title VisionSeal Complete - Python Startup
cls

echo ================================================================
echo 🎯 VisionSeal Complete - Python Direct Start
echo ================================================================

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo ❌ Virtual environment not found!
    echo Please run setup.bat first to create the virtual environment.
    pause
    exit /b 1
)

REM Activate virtual environment
echo 📦 Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if dependencies are installed
python -c "import fastapi" 2>nul
if errorlevel 1 (
    echo ❌ Dependencies not installed!
    echo Installing dependencies...
    pip install fastapi uvicorn pydantic pydantic-settings python-jose passlib python-multipart python-dotenv python-magic PyJWT
)

REM Run the Python server script
echo 🚀 Starting VisionSeal using Python script...
python run_server.py

pause