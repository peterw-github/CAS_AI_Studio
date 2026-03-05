#!/bin/bash
# Title: Voice Bridge Server

echo "Starting Voice Bridge..."
echo ""

SCRIPT_PATH="/mnt/slw_drive/Vaults/CAS_AI_Studio/Mini_Programs/Gboard_To_PC/gboard_server.py"
VENV_PYTHON="/mnt/slw_drive/Vaults/CAS_AI_Studio/.venv/bin/python"

if [ ! -f "$SCRIPT_PATH" ]; then
    echo "ERROR: Could not find 'gboard_server.py'."
    echo "Please make sure this file is located at: $(dirname "$SCRIPT_PATH"), or update the path in this script."
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

"$VENV_PYTHON" "$SCRIPT_PATH"

echo ""
echo "Server has stopped."
read -p "Press Enter to exit..."
