@echo off
echo Starting Cortana Migration Protocol...
python migrate_history.py
if %errorlevel% neq 0 (
    echo Migration Failed!
    pause
    exit /b %errorlevel%
)
echo Migration Successful. Transfer complete.
pause