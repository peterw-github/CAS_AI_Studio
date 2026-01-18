"""
Screen recording via OBS WebSocket for CAS.
"""

import time
import os
from obswebsocket import obsws, requests

from cas_core.clipboard import copy_file_to_clipboard


# OBS Configuration
OBS_HOST = "localhost"
OBS_PORT = 4455
OBS_PASSWORD = "abeUarkO5QZDkcJw"  # Update this if needed


def _wait_for_file_ready(filepath: str, timeout: int = 20) -> bool:
    """
    Wait for a file to finish being written (muxing complete).
    Returns True when file is ready.
    """
    print("[OBS] Waiting for file to finalize...")
    start_time = time.time()
    last_size = -1
    stable_checks = 0

    while time.time() - start_time < timeout:
        try:
            if not os.path.exists(filepath):
                time.sleep(0.5)
                continue

            current_size = os.path.getsize(filepath)

            # Not ready if 0 bytes
            if current_size == 0:
                time.sleep(1.0)
                continue

            # Check if size is stable
            if current_size == last_size:
                stable_checks += 1
                if stable_checks >= 2:
                    print(f"[OBS] File ready: {current_size / 1024:.2f} KB")
                    return True
            else:
                stable_checks = 0
                last_size = current_size

            time.sleep(1.0)

        except Exception as e:
            print(f"[OBS] Wait error: {e}")
            time.sleep(1.0)

    print(f"[OBS] Timeout waiting for file: {filepath}")
    return False


def record_screen(duration: int = 10) -> bool:
    """
    Record the screen using OBS.
    
    Args:
        duration: Recording duration in seconds
    
    Returns:
        True if recording succeeded and file is in clipboard
    """
    print(f"[OBS] Connecting...")

    try:
        ws = obsws(OBS_HOST, OBS_PORT, OBS_PASSWORD)
        ws.connect()

        # Start recording
        print(f"[OBS] Starting {duration}s recording...")
        ws.call(requests.StartRecord())

        # Wait
        time.sleep(duration)

        # Stop recording
        print("[OBS] Stopping...")
        response = ws.call(requests.StopRecord())

        # Get output path
        saved_path = response.datain.get('outputPath')
        ws.disconnect()

        if not saved_path:
            print("[OBS ERROR] No output path returned.")
            return False

        # Wait for file to finish writing
        if not _wait_for_file_ready(saved_path, timeout=30):
            print("[OBS ERROR] File never finished writing.")
            return False

        # Copy to clipboard
        if copy_file_to_clipboard(saved_path):
            print("[OBS] Success! Video in clipboard.")
            return True
        else:
            print("[OBS ERROR] Failed to copy to clipboard.")
            return False

    except Exception as e:
        print(f"[OBS ERROR] Connection failed: {e}")
        return False


if __name__ == "__main__":
    print("--- Testing OBS Recording ---")
    record_screen(5)
