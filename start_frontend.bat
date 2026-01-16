@echo off
echo ========================================
echo   Face Attendance System - Frontend
echo ========================================
echo.

cd frontend

REM Check if build exists
if not exist dist (
    echo Build folder not found. Building...
    call npm run build
)

echo.
echo Starting frontend server on http://localhost:3000
echo Press Ctrl+C to stop
echo.

REM Check if serve is installed
where serve >nul 2>nul
if errorlevel 1 (
    echo Installing serve...
    call npm install -g serve
)

REM Serve production build
serve -s dist -p 3000
