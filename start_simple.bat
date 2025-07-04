@echo off
title VisionSeal Complete - Simple Start
cls

echo ================================================================
echo 🎯 VisionSeal Complete - Simple Startup
echo ================================================================

REM Activate virtual environment
if exist "venv\Scripts\activate.bat" (
    echo 📦 Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo ❌ Virtual environment not found. Please run setup.bat first.
    pause
    exit /b 1
)

REM Set Python path to current directory
set PYTHONPATH=%CD%

echo 🚀 Starting VisionSeal...
echo Server will be available at: http://localhost:8080
echo.

REM Start the application directly with Python
python -c "
import sys
import os
sys.path.insert(0, os.getcwd())
sys.path.insert(0, os.path.join(os.getcwd(), 'src'))

try:
    from src.main import app
    import uvicorn
    print('✅ Application loaded successfully')
    print('🌐 Starting server on http://localhost:8080')
    uvicorn.run(app, host='0.0.0.0', port=8080, reload=True)
except ImportError as e:
    print(f'❌ Import Error: {e}')
    print('Current working directory:', os.getcwd())
    print('Python path:', sys.path[:3])
    input('Press Enter to exit...')
except Exception as e:
    print(f'❌ Error: {e}')
    input('Press Enter to exit...')
"

echo.
echo 🛑 Server stopped.
pause