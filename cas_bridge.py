"""
CAS Bridge - Selenium interface to AI Studio.

This module:
1. Monitors AI Studio for new messages
2. Copies them to the latest_message.md file
3. Reads the command queue and executes UI actions
"""

import time
import os
import datetime
import pyperclip

import cas_config as cfg
from cas_core import deserialize_responses
from cas_core.clipboard import copy_file_to_clipboard

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException


# --- CHROME CONNECTION ---

def connect_chrome():
    """Connect to Chrome instance running with remote debugging."""
    opt = Options()
    opt.add_experimental_option("debuggerAddress", cfg.CHROME_DEBUG_PORT)
    opt.add_argument("--disable-background-timer-throttling")
    opt.add_argument("--disable-renderer-backgrounding")
    opt.add_argument("--disable-backgrounding-occluded-windows")
    return webdriver.Chrome(options=opt)


def find_ai_studio_tab(driver):
    """Switch to the AI Studio tab if not already there."""
    if "AI Studio" not in driver.title:
        print("[BRIDGE] Searching for AI Studio tab...")
        for handle in driver.window_handles:
            driver.switch_to.window(handle)
            if "AI Studio" in driver.title:
                print(f"[BRIDGE] Found: {driver.title}")
                return True
    return True


# --- INPUT BOX HELPERS ---

def get_input_box(driver):
    """Find and click the chat input box."""
    box = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "textarea[aria-label='Enter a prompt']"))
    )
    box.click()
    return box


def submit_message(box):
    """Submit the current message."""
    box.send_keys(Keys.CONTROL, Keys.ENTER)


# --- MESSAGE READING ---

def check_for_new_message(driver):
    """Check for and capture new AI responses."""
    try:
        buttons = driver.find_elements(By.CSS_SELECTOR, "button[aria-label='Good response']")
        if not buttons:
            return
        
        latest = buttons[-1]
        
        # Check if already processed
        if driver.execute_script(
            "return arguments[0].getAttribute('data-cas-processed')", latest
        ) == "true":
            return
        
        # Copy via UI
        pyperclip.copy("")
        driver.execute_script(
            "arguments[0].closest('.chat-turn-container')"
            ".querySelector('button[aria-label=\"Open options\"]').click()",
            latest
        )
        WebDriverWait(driver, 2).until(
            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Copy as markdown')]"))
        ).click()
        
        # Wait for clipboard
        for _ in range(20):
            content = pyperclip.paste()
            if content.strip():
                # Write to file for brain
                with open(cfg.LATEST_MSG_FILE, "w", encoding="utf-8") as f:
                    f.write(content)
                
                # Log raw message
                _log_raw_message(content)
                
                # Mark as processed
                driver.execute_script(
                    "arguments[0].setAttribute('data-cas-processed', 'true')", latest
                )
                print(f"[BRIDGE] New message captured ({len(content)} chars).")
                return
            time.sleep(0.1)
    
    except StaleElementReferenceException:
        return  # DOM changed, try again next loop
    except Exception as e:
        print(f"[BRIDGE READ ERROR] {e}")


def _log_raw_message(content: str):
    """Log the raw message to a file for debugging."""
    try:
        os.makedirs("RawTextFiles", exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join("RawTextFiles", f"msg_{ts}.md")
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
            f.write("\n\n---\n\n### DEBUG: RAW REPR\n```python\n")
            f.write(repr(content))
            f.write("\n```")
    except Exception as e:
        print(f"[BRIDGE LOG ERROR] {e}")


# --- RESPONSE HANDLERS ---

def handle_text(box, text: str):
    """Type or paste text into the input box."""
    # Try clipboard first (faster)
    try:
        pyperclip.copy(text)
        box.click()
        box.send_keys(Keys.CONTROL, 'v')
        time.sleep(0.5)
        return True
    except:
        pass
    
    # Fallback to typing (works when screen is locked)
    print("[BRIDGE] Clipboard unavailable, typing directly...")
    try:
        box.send_keys(text)
        time.sleep(0.5)
        return True
    except Exception as e:
        print(f"[BRIDGE ERROR] Direct typing failed: {e}")
        return False


def handle_file_upload(box, path: str):
    """Upload a file by copying to clipboard and pasting."""
    if copy_file_to_clipboard(path):
        box.send_keys(Keys.CONTROL, 'v')
        time.sleep(2.0)
        return True
    return False


def handle_screenshot(box):
    """Take a screenshot and paste it."""
    from cas_logic.screen_snapshot import take_screenshot_to_clipboard
    
    if take_screenshot_to_clipboard():
        box.send_keys(Keys.CONTROL, 'v')
        time.sleep(1.5)
        return True
    return False


def handle_screen_record(box):
    """Paste the screen recording (already in clipboard from OBS)."""
    box.send_keys(Keys.CONTROL, 'v')
    print("[BRIDGE] Video pasted. Waiting for processing...")
    time.sleep(12.0)  # AI Studio needs time to process video
    return True


def handle_phone_photo(box):
    """Phone photo is already in clipboard from adb module."""
    box.send_keys(Keys.CONTROL, 'v')
    time.sleep(1.5)
    return True


def handle_phone_video(box):
    """Phone video is already in clipboard from adb module."""
    box.send_keys(Keys.CONTROL, 'v')
    print("[BRIDGE] Phone video pasted. Waiting for processing...")
    time.sleep(12.0)
    return True


def handle_delete_file(driver, filename: str):
    """Delete a message containing a file with the given filename."""
    try:
        print(f"[BRIDGE] Deleting file: '{filename}'")
        
        # Find the file span
        file_span = driver.find_element(
            By.CSS_SELECTOR, f"ms-file-chunk span.name[title='{filename}']"
        )
        turn = file_span.find_element(By.XPATH, "ancestor::ms-chat-turn")
        
        # Open options menu
        driver.execute_script(
            "arguments[0].querySelector('button[aria-label=\"Open options\"]').click()",
            turn
        )
        time.sleep(0.5)
        
        # Click delete
        WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.XPATH, "//span[text()='Delete']"))
        ).click()
        
        print(f"[BRIDGE] Deleted: {filename}")
        return True
        
    except Exception as e:
        print(f"[BRIDGE] Delete failed for '{filename}': {e}")
        return False


# --- MAIN PROCESSING ---

def process_command_queue(driver):
    """Process responses from the brain."""
    if os.path.getsize(cfg.COMMAND_FILE) == 0:
        return
    
    with open(cfg.COMMAND_FILE, "r+", encoding="utf-8") as f:
        content = f.read().strip()
        if not content:
            return
        
        print("[BRIDGE] Processing command queue...")
        
        # Parse responses
        responses = deserialize_responses(content)
        if not responses:
            print("[BRIDGE] Could not parse responses")
            f.truncate(0)
            return
        
        # Get input box
        try:
            box = get_input_box(driver)
        except Exception as e:
            print(f"[BRIDGE] Could not find input box: {e}")
            return
        
        # Process each response
        text_parts = []
        has_file_attachment = False
        
        for resp in responses:
            resp_type = resp.get('type')
            
            if resp_type == 'text':
                text_parts.append(resp['text'])
            
            elif resp_type == 'file_upload':
                handle_file_upload(box, resp['path'])
                has_file_attachment = True
                text_parts.append(resp['message'])
            
            elif resp_type == 'screenshot':
                handle_screenshot(box)
                has_file_attachment = True
                text_parts.append(resp['message'])
            
            elif resp_type == 'screen_record':
                handle_screen_record(box)
                has_file_attachment = True
                text_parts.append(resp['message'])
            
            elif resp_type == 'phone_photo':
                handle_phone_photo(box)
                has_file_attachment = True
                text_parts.append(resp['message'])
            
            elif resp_type == 'phone_video':
                handle_phone_video(box)
                has_file_attachment = True
                text_parts.append(resp['message'])
            
            elif resp_type == 'delete_file':
                handle_delete_file(driver, resp['filename'])
        
        # Send accumulated text
        if text_parts:
            full_text = "\n\n".join(text_parts)
            handle_text(box, full_text)
        
        # Wait for AI Studio to process file attachments
        if has_file_attachment:
            print(f"[BRIDGE] File attached. Waiting {cfg.FILE_ATTACHMENT_WAIT}s for AI Studio processing...")
            time.sleep(cfg.FILE_ATTACHMENT_WAIT)
        
        # Submit
        print("[BRIDGE] Submitting...")
        submit_message(box)
        
        # Clear queue
        f.seek(0)
        f.truncate(0)


# --- MAIN LOOP ---

def main():
    print("--- CAS BRIDGE ---")
    
    driver = connect_chrome()
    print(f"[BRIDGE] Connected to: {driver.title}")
    find_ai_studio_tab(driver)
    
    # Ensure command file exists
    if not os.path.exists(cfg.COMMAND_FILE):
        open(cfg.COMMAND_FILE, 'w').close()
    
    while True:
        # 1. Check for new messages from AI
        check_for_new_message(driver)
        
        # 2. Process command queue from brain
        process_command_queue(driver)
        
        time.sleep(cfg.BRIDGE_LOOP_DELAY)


if __name__ == "__main__":
    main()
