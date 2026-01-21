"""
Scheduler for CAS brain timing and heartbeat logic.

Handles:
- Heartbeat intervals
- Sleep with interrupt detection
- Message file monitoring
- Ambient capture coordination
"""

import os
import time
from typing import Callable, Optional, Tuple
from dataclasses import dataclass

import cas_config as cfg


def get_message_mtime() -> float:
    """Get modification time of the latest message file."""
    if os.path.exists(cfg.LATEST_MSG_FILE):
        return os.path.getmtime(cfg.LATEST_MSG_FILE)
    return 0


def read_latest_message() -> str:
    """Read the contents of the latest message file."""
    try:
        with open(cfg.LATEST_MSG_FILE, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"[SCHEDULER] Error reading message: {e}")
        return ""


def smart_wait(seconds: float, last_mtime: float) -> bool:
    """
    Sleep for the specified duration, but wake early if a new message arrives.
    
    Args:
        seconds: How long to sleep
        last_mtime: The mtime to compare against (to detect new messages)
    
    Returns:
        True if interrupted by new message, False if timer completed normally
    """
    if seconds <= 0:
        return False

    # Show target wake time
    target_time = time.time() + seconds
    target_str = time.strftime("%H:%M:%S", time.localtime(target_time))
    print(f"[SCHEDULER] Sleeping {int(seconds)}s... (Next Pulse: {target_str})")

    start = time.time()
    last_status_update = start

    while time.time() - start < seconds:
        # Check for new message (interrupt)
        if get_message_mtime() > last_mtime:
            print("\n[SCHEDULER] Interrupt detected!")
            return True

        # Status update every 60 seconds
        now = time.time()
        if now - last_status_update >= 60:
            remaining = int(seconds - (now - start))
            if remaining > 10:
                mins = remaining // 60
                secs = remaining % 60
                print(f"[SCHEDULER] ... {mins}m {secs:02d}s remaining ...")
            last_status_update = now

        time.sleep(1)

    print("[SCHEDULER] Timer finished.")
    return False


class HeartbeatScheduler:
    """
    Manages heartbeat timing for the CAS brain.
    
    Handles:
    - Tracking next heartbeat time
    - Detecting if we should send immediately vs wait
    - Adjusting interval dynamically
    - Coordinating ambient capture sequence
    """
    
    # Ambient capture starts this many seconds before heartbeat
    AMBIENT_LEAD_TIME = 30
    
    def __init__(self, interval_seconds: int):
        self.interval = interval_seconds
        self.next_heartbeat = time.time()
        self.last_mtime = get_message_mtime()
        
        # Ambient capture integration
        self._ambient_capture = None
        self._ambient_data = None
    
    def _get_ambient_capture(self):
        """Lazy-load ambient capture module."""
        if self._ambient_capture is None:
            try:
                from cas_core.ambient import get_ambient_capture
                self._ambient_capture = get_ambient_capture()
            except ImportError as e:
                print(f"[SCHEDULER] Ambient capture not available: {e}")
        return self._ambient_capture
    
    def set_interval(self, seconds: int):
        """Update the heartbeat interval."""
        self.interval = seconds
        self.next_heartbeat = time.time() + seconds
    
    def is_heartbeat_due(self) -> bool:
        """Check if it's time to send a heartbeat."""
        return time.time() >= self.next_heartbeat
    
    def schedule_next(self):
        """Schedule the next heartbeat from now."""
        self.next_heartbeat = time.time() + self.interval
        
        # Note: We do NOT clear ambient data here anymore.
        # Files need to persist until the bridge processes them.
        # They will be cleared at the start of the next capture sequence.
    
    def wait_for_next(self) -> bool:
        """
        Wait until next heartbeat or new message.
        
        Integrates ambient capture: if enabled and interval >= 30s,
        will run capture sequence in the final 30 seconds.
        
        Returns True if interrupted by new message.
        """
        remaining = self.next_heartbeat - time.time()
        
        # Get ambient capture instance
        ambient = self._get_ambient_capture()
        ambient_enabled = ambient and ambient.is_enabled()
        
        # Check if we should do ambient capture
        # Only if: enabled, interval >= 30s, and we have enough time
        should_capture = (
            ambient_enabled and 
            self.interval >= self.AMBIENT_LEAD_TIME and
            remaining > self.AMBIENT_LEAD_TIME
        )
        
        if should_capture:
            # Phase 1: Wait until T-30s (before ambient capture starts)
            wait_before_ambient = remaining - self.AMBIENT_LEAD_TIME
            
            if wait_before_ambient > 0:
                print(f"[SCHEDULER] Waiting {int(wait_before_ambient)}s, then ambient capture begins...")
                interrupted = smart_wait(wait_before_ambient, self.last_mtime)
                
                if interrupted:
                    self.last_mtime = get_message_mtime()
                    return True
            
            # Phase 2: Run ambient capture sequence (30 seconds)
            print("[SCHEDULER] Entering ambient capture window...")
            
            def check_interrupt():
                return get_message_mtime() > self.last_mtime
            
            self._ambient_data = ambient.run_capture_sequence(check_interrupt)
            
            if self._ambient_data is None:
                # Capture was interrupted
                self.last_mtime = get_message_mtime()
                return True
            
            # Capture complete, heartbeat is now due
            return False
        
        else:
            # No ambient capture - just wait normally
            if ambient_enabled and self.interval < self.AMBIENT_LEAD_TIME:
                print(f"[SCHEDULER] Ambient mode skipped (interval {self.interval}s < {self.AMBIENT_LEAD_TIME}s)")
            
            interrupted = smart_wait(remaining, self.last_mtime)
            
            if interrupted:
                self.last_mtime = get_message_mtime()
            
            return interrupted
    
    def get_ambient_data(self):
        """
        Get captured ambient data (if any).
        
        Returns AmbientData object or None.
        """
        return self._ambient_data
    
    def has_ambient_data(self) -> bool:
        """Check if we have ambient data to send."""
        return self._ambient_data is not None and (
            len(self._ambient_data.screenshot_paths) > 0 or 
            self._ambient_data.audio_path is not None
        )
    
    def update_mtime(self):
        """Update the tracked message mtime (call after processing)."""
        self.last_mtime = get_message_mtime()
        
        # Cancel any in-progress ambient capture
        ambient = self._get_ambient_capture()
        if ambient:
            if ambient._audio_recorder or len(ambient.data.screenshot_paths) > 0:
                print("[SCHEDULER] Cancelling ambient capture due to conversation activity")
            ambient.cancel()
            self._ambient_data = None
    
    def adjust_for_recent_activity(self):
        """
        If there was recent conversation, adjust next heartbeat accordingly.
        Called at startup.
        """
        time_since_last = time.time() - self.last_mtime
        
        if time_since_last < self.interval:
            # Recent activity - wait the remaining time
            remaining = self.interval - time_since_last
            self.next_heartbeat = time.time() + remaining
            print(f"[SCHEDULER] Recent activity ({int(time_since_last)}s ago). "
                  f"Next heartbeat in {int(remaining)}s.")
        else:
            # No recent activity - send immediately
            self.next_heartbeat = time.time()
            print("[SCHEDULER] No recent activity. Sending heartbeat now.")
