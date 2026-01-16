@echo off
echo ========================================
echo   MongoDB Backup Script
echo ========================================
echo.

REM Create backups folder if not exists
if not exist backups mkdir backups

REM Get current date
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set BACKUP_DATE=%datetime:~0,8%

echo Backing up MongoDB database: tugas_production
echo Backup date: %BACKUP_DATE%
echo.

REM Backup MongoDB
mongodump --db tugas_production --out backups\backup_%BACKUP_DATE%

if errorlevel 1 (
    echo.
    echo ERROR: Backup failed!
    echo Make sure MongoDB is running and mongodump is in PATH
    pause
    exit /b 1
)

echo.
echo Backup completed successfully!
echo Location: backups\backup_%BACKUP_DATE%
echo.

REM Keep only last 7 backups
echo Cleaning old backups (keeping last 7)...
forfiles /p backups /d -7 /c "cmd /c if @isdir==TRUE rd /s /q @path" 2>nul

echo.
echo Done!
pause
