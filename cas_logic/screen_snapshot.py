"""
Screenshot capture for CAS.
"""

import mss
from PIL import Image

import cas_config as cfg
from cas_core.clipboard import copy_image_to_clipboard


def take_screenshot_to_clipboard() -> bool:
    """
    Capture screen(s) and copy to clipboard.
    
    Uses cfg.MONITORS to determine which monitor(s):
    - 0 = all monitors
    - 1, 2, 3 = specific monitor
    
    Returns True on success.
    """
    try:
        with mss.mss() as sct:
            monitor = sct.monitors[cfg.MONITORS]
            print(f"[VISION] Capturing: {monitor}")
            
            sct_img = sct.grab(monitor)
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            
            return copy_image_to_clipboard(img)
            
    except Exception as e:
        print(f"[VISION ERROR] {e}")
        return False


if __name__ == "__main__":
    print("--- Testing Screenshot ---")
    take_screenshot_to_clipboard()
