@echo off
title VisionSeal Complete - Final Working Version
cls

echo ================================================================
echo 🎯 VisionSeal Complete - Final Working Version
echo ================================================================

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo 📦 Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ❌ Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo 📦 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo 📦 Installing dependencies...
pip install fastapi uvicorn pydantic pydantic-settings python-jose passlib python-multipart python-dotenv python-magic PyJWT --quiet

REM Fix imports automatically
if exist "fix_imports.py" (
    echo 🔧 Fixing relative imports...
    python fix_imports.py
) else (
    echo ⚠️ Import fixer not found, continuing anyway...
)

REM Check if standalone main file exists
if not exist "main_standalone.py" (
    echo ❌ main_standalone.py not found!
    echo Please ensure all files are copied correctly.
    pause
    exit /b 1
)

echo.
echo ✅ Setup complete!
echo.
echo 🚀 Starting VisionSeal Complete...
echo 📍 Server will be available at: http://localhost:8080
echo 📖 API Documentation at: http://localhost:8080/docs
echo 💚 Health Check at: http://localhost:8080/health
echo.
echo 💡 Press Ctrl+C to stop the server
echo ================================================================
echo.

REM Run the standalone version
python main_standalone.py

echo.
echo 🛑 Server stopped.
pause