@echo off
title VisionSeal Complete - One-Time Setup
cls

echo ================================================================
echo 🎯 VisionSeal Complete - One-Time Setup
echo ================================================================
echo This will set up everything needed to run VisionSeal
echo ================================================================
echo.

echo 🔧 Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found! 
    echo.
    echo Please install Python 3.9+ from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Python %PYTHON_VERSION% found

echo.
echo 🔧 Creating virtual environment...
if exist "venv" (
    echo Virtual environment already exists, removing old one...
    rmdir /s /q venv
)

python -m venv venv
if errorlevel 1 (
    echo ❌ Failed to create virtual environment
    echo.
    echo This might happen if:
    echo - Python is not properly installed
    echo - You don't have write permissions in this folder
    echo - Antivirus is blocking the operation
    echo.
    pause
    exit /b 1
)
echo ✅ Virtual environment created

echo.
echo 📦 Activating virtual environment and installing dependencies...
call venv\Scripts\activate.bat

echo Installing core FastAPI dependencies...
pip install fastapi uvicorn --quiet

echo Installing Pydantic for data validation...
pip install pydantic pydantic-settings --quiet

echo Installing security dependencies...
pip install python-jose passlib PyJWT --quiet

echo Installing file handling dependencies...
pip install python-multipart python-magic --quiet

echo Installing configuration dependencies...
pip install python-dotenv --quiet

if errorlevel 1 (
    echo ❌ Failed to install some dependencies
    echo.
    echo Try running: pip install --upgrade pip
    echo Then run this setup again.
    echo.
    pause
    exit /b 1
)

echo ✅ All dependencies installed successfully

echo.
echo 🔍 Verifying installation...
python -c "import fastapi, uvicorn, pydantic; print('✅ Core dependencies working')" 2>nul
if errorlevel 1 (
    echo ❌ Installation verification failed
    pause
    exit /b 1
)

echo.
echo 🔧 Creating necessary directories...
if not exist "data" mkdir data
if not exist "logs" mkdir logs  
if not exist "uploads" mkdir uploads
if not exist "uploads\temp" mkdir uploads\temp
if not exist "data\extractions" mkdir data\extractions
if not exist "data\ai_responses" mkdir data\ai_responses
echo ✅ Directories created

echo.
echo ================================================================
echo ✅ Setup Complete!
echo ================================================================
echo.
echo You can now run VisionSeal by double-clicking: start.bat
echo.
echo 📍 The application will be available at:
echo    • Main Interface: http://localhost:8080
echo    • API Documentation: http://localhost:8080/docs
echo.
echo 🛡️ Security Features Included:
echo    • Input validation and sanitization
echo    • Secure file upload handling  
echo    • Rate limiting protection
echo    • CORS security
echo    • Structured logging
echo.
echo ================================================================
pause