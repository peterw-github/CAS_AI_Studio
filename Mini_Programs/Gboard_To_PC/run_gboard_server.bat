@echo off
title Voice Bridge Server
echo Starting Voice Bridge...
echo.

:: Check if the script exists in the current folder
if not exist "D:\CAS\Mini_Programs\Gboard_To_PC\gboard_server.py" (
    echo ERROR: Could not find 'gboard_server.py'.
    echo Please make sure this file is located at: D:\CAS\Mini_Programs\Gboard_To_PC, or update the path in this bat file.
    echo.
    pause
    exit /b
)

:: Run the script using the Virtual Environment Python found in your logs
"D:\CAS\.venv\Scripts\python.exe" "D:\CAS\Mini_Programs\Gboard_To_PC\gboard_server.py"

:: Pause if it closes so you can see errors
echo.
echo Server has stopped.
pause