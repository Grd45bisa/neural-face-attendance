@echo off
REM Quick setup script for Flask backend

echo ========================================
echo Flask Backend Setup
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from python.org
    pause
    exit /b 1
)

echo [1/5] Creating virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

echo [2/5] Activating virtual environment...
call venv\Scripts\activate.bat

echo [3/5] Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo [4/5] Creating .env file...
if not exist .env (
    copy .env.example .env
    echo .env file created. Please edit it with your settings.
) else (
    echo .env file already exists.
)

echo [5/5] Creating data directory...
if not exist ..\data (
    mkdir ..\data
    echo Data directory created.
)

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Make sure MongoDB is installed and running
echo 2. Edit .env file with your configuration
echo 3. Run: python app.py
echo.
echo For MongoDB installation:
echo - Download from: https://www.mongodb.com/try/download/community
echo - Start service: net start MongoDB
echo.
pause
