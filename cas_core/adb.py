"""
ADB (Android Debug Bridge) utilities for phone communication.

Handles:
- Wireless connection to phone
- Taking photos via phone camera
- Recording video via phone camera
"""

import subprocess
import time
import os
import requests
from PIL import Image
import io

from cas_core.clipboard import copy_file_to_clipboard, copy_image_to_clipboard


# --- CONFIGURATION ---
PHONE_IP = "192.168.0.235"
ADB_PORT = "5555"
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADB_PATH = os.path.join(_BASE_DIR, "Phone_Code", "android_sdk_platform_tools", "adb.exe")
PC_DESTINATION_FOLDER = os.path.join(_BASE_DIR, "Phone_Code", "Recordings")

# Phone camera app coordinates
COORD_WIDE_LENS = "1550 630"
COORD_SAVE_TICK = "1850 553"

# IP Webcam snapshot endpoint
PHONE_SNAPSHOT_URL = f"http://{PHONE_IP}:8080/snap"


def _run_adb(command_string: str, return_output: bool = False):
    """Execute an ADB command."""
    if not os.path.exists(ADB_PATH):
        print(f"[ADB] Error: ADB executable not found at {ADB_PATH}")
        return None

    full_cmd = f'"{ADB_PATH}" {command_string}'
    try:
        result = subprocess.run(
            full_cmd, shell=True, check=True, 
            capture_output=True, text=True
        )
        if return_output:
            return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"[ADB] Command failed: {e}")
        return None


def _connect_wireless() -> bool:
    """Establish wireless ADB connection to phone."""
    print(f"[ADB] Connecting to phone ({PHONE_IP})...")
    _run_adb("disconnect")  # Clear stale connections
    output = _run_adb(f"connect {PHONE_IP}:{ADB_PORT}", return_output=True)
    
    if output and f"connected to {PHONE_IP}" in output:
        print("[ADB] Connected.")
        return True
    
    print("[ADB] Connection failed.")
    return False


def _get_camera_files() -> set:
    """List video files in phone's camera folder."""
    output = _run_adb("shell ls /sdcard/DCIM/Camera/", return_output=True)
    if not output:
        return set()
    return {f for f in output.splitlines() if f.endswith(".mp4")}


# --- PUBLIC API ---

def take_phone_snapshot() -> bool:
    """
    Fetch a snapshot from the phone's IP Webcam app.
    Copies the image to clipboard.
    
    Returns True on success.
    """
    try:
        print(f"[PHONE] Fetching snapshot from {PHONE_SNAPSHOT_URL}...")
        response = requests.get(PHONE_SNAPSHOT_URL, timeout=3)

        if response.status_code == 200:
            image = Image.open(io.BytesIO(response.content))
            success = copy_image_to_clipboard(image)
            if success:
                print("[PHONE] Snapshot captured and copied to clipboard.")
            return success
        else:
            print(f"[PHONE ERROR] HTTP {response.status_code}")
            return False

    except requests.exceptions.Timeout:
        print("[PHONE ERROR] Connection timeout - is IP Webcam running?")
        return False
    except Exception as e:
        print(f"[PHONE ERROR] {e}")
        return False


def record_phone_video(duration_seconds: int = 10) -> bool:
    """
    Record video using the phone's camera app via ADB.
    Pulls the file to PC and copies to clipboard.
    
    Returns True on success.
    """
    # 1. Connect
    if not _connect_wireless():
        return False

    # 2. Get file list (before recording)
    print("[ADB] Scanning existing files...")
    files_before = _get_camera_files()

    print(f"[ADB] Recording {duration_seconds}s video...")

    # 3. Wake phone and unlock
    _run_adb("shell input keyevent 224")  # Wake
    _run_adb("shell input swipe 500 1500 500 500")  # Unlock swipe
    time.sleep(1)

    # 4. Open camera and configure
    _run_adb("shell am start -a android.media.action.VIDEO_CAPTURE")
    time.sleep(0.5)
    _run_adb(f"shell input tap {COORD_WIDE_LENS}")  # Wide angle lens
    time.sleep(0.5)

    # 5. Record
    _run_adb("shell input keyevent 24")  # Start (volume up)
    time.sleep(duration_seconds)
    _run_adb("shell input keyevent 24")  # Stop

    time.sleep(0.5)
    _run_adb(f"shell input tap {COORD_SAVE_TICK}")  # Confirm save

    print("[ADB] Waiting for file to finalize...")
    time.sleep(3)

    # 6. Find new file
    files_after = _get_camera_files()
    new_files = files_after - files_before

    if not new_files:
        print("[ADB ERROR] No new video file detected.")
        return False

    new_video = list(new_files)[0]
    phone_path = f"/sdcard/DCIM/Camera/{new_video}"
    local_path = os.path.join(PC_DESTINATION_FOLDER, new_video)

    # 7. Ensure destination folder exists
    os.makedirs(PC_DESTINATION_FOLDER, exist_ok=True)

    # 8. Pull file to PC
    print(f"[ADB] Pulling {new_video}...")
    _run_adb(f'pull "{phone_path}" "{local_path}"')

    # 9. Copy to clipboard
    if os.path.exists(local_path):
        success = copy_file_to_clipboard(local_path)
        if success:
            print("[ADB] Video ready in clipboard.")
            return True

    print("[ADB ERROR] Failed to retrieve video file.")
    return False


if __name__ == "__main__":
    # Quick test
    print("--- Testing Phone Snapshot ---")
    take_phone_snapshot()
