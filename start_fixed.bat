@echo off
title VisionSeal Complete - Fixed Startup
cls

echo ================================================================
echo 🎯 VisionSeal Complete - Fixed Python Start
echo ================================================================

REM Check if we're in the right directory
if not exist "src\main.py" (
    echo ❌ main.py not found in src directory!
    echo Make sure you're in the VisionSeal-Refactored directory
    echo and that all files were copied correctly.
    pause
    exit /b 1
)

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

REM Check if main dependencies are installed
python -c "import fastapi, uvicorn" 2>nul
if errorlevel 1 (
    echo ❌ Dependencies not installed!
    echo Installing core dependencies...
    pip install fastapi uvicorn pydantic pydantic-settings python-jose passlib python-multipart python-dotenv python-magic PyJWT
    if errorlevel 1 (
        echo ❌ Failed to install dependencies
        pause
        exit /b 1
    )
)

REM Run the fixed Python server script
echo 🚀 Starting VisionSeal using fixed Python script...
python run_server_fixed.py

pause