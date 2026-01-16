@echo off
echo ========================================
echo   Face Attendance System - Backend
echo ========================================
echo.

cd backend

REM Check if virtual environment exists
if exist venv (
    echo Activating virtual environment...
    call venv\Scripts\activate
) else (
    echo WARNING: Virtual environment not found
    echo Run: python -m venv venv
    pause
    exit /b 1
)

REM Set environment to production
set FLASK_ENV=production
set FLASK_DEBUG=False

echo.
echo Starting backend server on http://localhost:5000
echo Press Ctrl+C to stop
echo.

REM Start server with waitress (production)
waitress-serve --host=0.0.0.0 --port=5000 app:app

REM If waitress not installed, fallback to Flask dev server
if errorlevel 1 (
    echo.
    echo Waitress not found. Installing...
    pip install waitress
    waitress-serve --host=0.0.0.0 --port=5000 app:app
)
