@echo off

:: --- CONFIGURATION ---
:: Note: I removed the quotes from the variable definitions here
:: so we can safely wrap them in quotes later.
set WORK_DIR=%~dp0
set PYTHON_EXE=%~dp0.venv\Scripts\python.exe

:: --- LAUNCH WINDOWS TERMINAL ---
:: Syntax breakdown:
:: 1. wt : Launches Windows Terminal
:: 2. --title : Names the first tab
:: 3. -d : Sets the directory
:: 4. cmd /k : Runs the python script and KEEPS THE TAB OPEN (/k) if it crashes
:: 5. ; new-tab : Tells terminal to open a second tab in the same window

wt --title "CAS BRIDGE" -d "%WORK_DIR%" cmd /k "%PYTHON_EXE% cas_bridge.py" ; new-tab --title "CAS BRAIN" -d "%WORK_DIR%" cmd /k "%PYTHON_EXE% cas_brain.py"

:: --- DONE ---
:: No pause needed, as the WT window opens separately.