@echo off
REM GitSee Startup Script (Windows)

echo ========================================
echo Starting GitSee Service...
echo ========================================
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found
    echo Please install Python 3.7 or higher
    echo.
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Detected Python version: %PYTHON_VERSION%

REM Change to script directory
cd /d "%~dp0"

REM Check if first run
if not exist "data\gitsee.db" (
    echo.
    echo First run detected, initializing...
    echo.
    python setup.py
    if errorlevel 1 (
        echo.
        echo Initialization failed, please check error messages above
        pause
        exit /b 1
    )
    echo.
)

REM Start Flask application
echo Starting Web service...
echo Access URL: http://localhost:5000
echo Press Ctrl+C to stop service
echo.

REM Wait a moment for service to start, then open browser
start /b python backend\app.py

REM Wait 3 seconds for service to initialize
timeout /t 3 /nobreak >nul

REM Open default browser to GitSee
echo Opening browser...
start http://localhost:5000

echo.
echo Service is running. Press Ctrl+C to stop.

REM Keep script running
python -c "import time; time.sleep(999999)"
