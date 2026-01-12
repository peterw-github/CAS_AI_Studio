@echo off
title Voice Bridge Server
echo Starting Voice Bridge...
echo.

:: Check if the python script is actually in the folder
if not exist "gboard_server.py" (
    echo ERROR: Could not find 'gboard_server.py'.
    echo Please make sure this file is in the same folder as your Python script.
    echo.
    pause
    exit /b
)

:: Run the script
:: This will stay open until you close the window or press Ctrl+C
python gboard_server.py

:: If the script crashes or closes, pause so you can see the error
echo.
echo Server has stopped.
pause