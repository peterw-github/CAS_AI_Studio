"""
Scheduler for CAS brain timing and heartbeat logic.

Handles:
- Heartbeat intervals
- Sleep with interrupt detection
- Message file monitoring
"""

import os
import time
from typing import Callable, Optional

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
    """
    
    def __init__(self, interval_seconds: int):
        self.interval = interval_seconds
        self.next_heartbeat = time.time()
        self.last_mtime = get_message_mtime()
    
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
    
    def wait_for_next(self) -> bool:
        """
        Wait until next heartbeat or new message.
        
        Returns True if interrupted by new message.
        """
        remaining = self.next_heartbeat - time.time()
        interrupted = smart_wait(remaining, self.last_mtime)
        
        if interrupted:
            self.last_mtime = get_message_mtime()
        
        return interrupted
    
    def update_mtime(self):
        """Update the tracked message mtime (call after processing)."""
        self.last_mtime = get_message_mtime()
    
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
