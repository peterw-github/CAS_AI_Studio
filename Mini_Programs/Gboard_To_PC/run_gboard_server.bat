@echo off
title Voice Bridge Server
echo Starting Voice Bridge...
echo.

:: Check if the script exists in the current folder
if not exist "gboard_server.py" (
    echo ERROR: Could not find 'gboard_server.py'.
    echo Please make sure this file is in the same folder as your Python script.
    echo.
    pause
    exit /b
)

:: Run the script using the Virtual Environment Python found in your logs
"D:\CAS\.venv\Scripts\python.exe" "gboard_server.py"

:: Pause if it closes so you can see errors
echo.
echo Server has stopped.
pause