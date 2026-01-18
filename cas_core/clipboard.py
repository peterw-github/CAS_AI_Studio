"""
Unified clipboard utilities for CAS.

Consolidates clipboard operations that were previously scattered across:
- upload_file.py
- screen_snapshot.py  
- what_john_sees_snapshot.py
"""

import os
import struct
import io
import win32clipboard
from PIL import Image


def copy_file_to_clipboard(file_path: str) -> bool:
    """
    Copy a file to the Windows clipboard (CF_HDROP format).
    Used for uploading files to chat via paste.
    """
    try:
        file_path = os.path.abspath(file_path)
        if not os.path.exists(file_path):
            print(f"[CLIPBOARD] File not found: {file_path}")
            return False

        # Build Windows CF_HDROP structure
        files = (file_path + "\0\0").encode('utf-16-le')
        header = struct.pack("IIIII", 20, 0, 0, 0, 1)
        data = header + files

        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(15, data)  # 15 = CF_HDROP
        win32clipboard.CloseClipboard()
        
        print(f"[CLIPBOARD] File copied: {os.path.basename(file_path)}")
        return True
        
    except Exception as e:
        print(f"[CLIPBOARD ERROR] {e}")
        return False


def copy_image_to_clipboard(image: Image.Image) -> bool:
    """
    Copy a PIL Image to the Windows clipboard (CF_DIB format).
    Used for screenshots and phone camera images.
    """
    try:
        # Convert to BMP buffer (clipboard format)
        output = io.BytesIO()
        image.convert("RGB").save(output, "BMP")
        data = output.getvalue()[14:]  # Skip BMP header
        output.close()

        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
        win32clipboard.CloseClipboard()
        
        print(f"[CLIPBOARD] Image copied ({image.size[0]}x{image.size[1]})")
        return True
        
    except Exception as e:
        print(f"[CLIPBOARD ERROR] {e}")
        return False


def copy_image_bytes_to_clipboard(image_bytes: bytes) -> bool:
    """
    Copy raw image bytes (e.g., from HTTP response) to clipboard.
    Converts to PIL Image first, then to clipboard.
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))
        return copy_image_to_clipboard(image)
    except Exception as e:
        print(f"[CLIPBOARD ERROR] {e}")
        return False
