"""
Ambient Capture System for CAS.

Orchestrates the capture of screenshots and audio in the lead-up to a heartbeat,
providing the AI with temporal context about what's been happening.

Captures:
- Screenshot at T-30s
- Screenshot at T-20s  
- Screenshot at T-10s
- Screenshot at T-0s (heartbeat time)
- Audio recording of the full 30 seconds

All 4 screenshots are sent individually to the chat.
"""

import os
import time
from dataclasses import dataclass, field
from typing import List, Optional
from PIL import Image

import cas_config as cfg


@dataclass
class AmbientData:
    """Container for captured ambient data."""
    screenshot_paths: List[str] = field(default_factory=list)  # Paths to screenshot files
    screenshot_labels: List[str] = field(default_factory=list)  # Labels for each screenshot
    audio_path: Optional[str] = None  # Path to audio file
    capture_times: List[float] = field(default_factory=list)  # Timestamps of each capture
    
    def clear(self):
        """Clear all data and delete temp files."""
        for path in self.screenshot_paths:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception as e:
                print(f"[AMBIENT] Failed to delete {path}: {e}")
        
        if self.audio_path:
            try:
                if os.path.exists(self.audio_path):
                    os.remove(self.audio_path)
            except Exception as e:
                print(f"[AMBIENT] Failed to delete {self.audio_path}: {e}")
        
        self.screenshot_paths = []
        self.screenshot_labels = []
        self.audio_path = None
        self.capture_times = []
    
    def is_complete(self) -> bool:
        """Check if we have all expected captures."""
        return len(self.screenshot_paths) == 4


class AmbientCapture:
    """
    Manages ambient context capture for heartbeats.
    
    When enabled, captures screenshots at T-30, T-20, T-10, and T-0 seconds
    before heartbeat, plus continuous audio for the full 30 seconds.
    """
    
    # Capture schedule (seconds before heartbeat)
    CAPTURE_OFFSETS = [30, 20, 10, 0]
    CAPTURE_LABELS = ["T-30s", "T-20s", "T-10s", "T-0s"]
    AUDIO_DURATION = 30
    
    def __init__(self):
        self.enabled = getattr(cfg, 'AMBIENT_MODE_DEFAULT', True)
        self.temp_dir = getattr(cfg, 'AMBIENT_TEMP_DIR', 'ambient_temp')
        self.data = AmbientData()
        
        self._audio_recorder = None
        self._cancelled = False
        
        # Ensure temp directory exists
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def is_enabled(self) -> bool:
        """Check if ambient mode is enabled."""
        return self.enabled
    
    def toggle(self) -> bool:
        """Toggle ambient mode. Returns new state."""
        self.enabled = not self.enabled
        print(f"[AMBIENT] Mode {'enabled' if self.enabled else 'disabled'}")
        return self.enabled
    
    def set_enabled(self, state: bool):
        """Explicitly set ambient mode state."""
        self.enabled = state
        print(f"[AMBIENT] Mode {'enabled' if self.enabled else 'disabled'}")
    
    def start_audio(self) -> bool:
        """Start the background audio recording."""
        try:
            from cas_logic.audio_capture import AudioRecorder
            
            self._audio_recorder = AudioRecorder()
            success = self._audio_recorder.start()
            
            if success:
                print("[AMBIENT] Audio recording started")
            
            return success
            
        except Exception as e:
            print(f"[AMBIENT] Failed to start audio: {e}")
            return False
    
    def capture_screenshot(self, label: str) -> Optional[str]:
        """
        Capture a screenshot and save to temp file.
        
        Args:
            label: Label for this screenshot (e.g., "T-30s")
        
        Returns path to saved file or None on failure.
        """
        try:
            import mss
            
            with mss.mss() as sct:
                # Always capture all monitors for ambient (cfg.MONITORS = 0)
                monitor = sct.monitors[0]
                sct_img = sct.grab(monitor)
                img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                
                # Save to file
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                index = len(self.data.screenshot_paths)
                filepath = os.path.join(self.temp_dir, f"ambient_ss_{timestamp}_{index}.png")
                
                img.save(filepath, "PNG")
                
                self.data.screenshot_paths.append(filepath)
                self.data.screenshot_labels.append(label)
                self.data.capture_times.append(time.time())
                
                print(f"[AMBIENT] Screenshot {index + 1}/4 saved ({label})")
                return filepath
                
        except Exception as e:
            print(f"[AMBIENT] Screenshot failed: {e}")
            return None
    
    def stop_audio(self) -> Optional[str]:
        """Stop audio recording and save to file."""
        if self._audio_recorder:
            if self._audio_recorder.is_recording():
                filepath = self._audio_recorder.stop(self.temp_dir)
                if filepath:
                    self.data.audio_path = filepath
                    print(f"[AMBIENT] Audio saved: {filepath}")
                else:
                    print("[AMBIENT] Audio recording returned no file")
                self._audio_recorder = None
                return filepath
            else:
                print("[AMBIENT] Audio recorder exists but is not recording")
                self._audio_recorder = None
        else:
            print("[AMBIENT] No audio recorder to stop")
        return None
    
    def cancel(self):
        """Cancel any in-progress capture and clear data."""
        self._cancelled = True
        
        # Stop audio if recording
        if self._audio_recorder:
            self._audio_recorder.cancel()
            self._audio_recorder = None
        
        # Clear captured data
        self.data.clear()
        
        print("[AMBIENT] Capture cancelled")
    
    def reset(self):
        """Reset for next capture cycle."""
        self._cancelled = False
    
    def run_capture_sequence(self, check_interrupt: callable) -> Optional[AmbientData]:
        """
        Run the full 30-second capture sequence.
        
        Args:
            check_interrupt: Callable that returns True if we should abort
                           (e.g., new message arrived)
        
        Returns:
            AmbientData with captured files, or None if interrupted/failed
        """
        self._cancelled = False
        self.data.clear()  # Clear old files from previous capture
        
        print("[AMBIENT] Starting 30-second capture sequence...")
        
        # Start audio recording
        audio_started = self.start_audio()
        if not audio_started:
            print("[AMBIENT] Warning: Audio recording failed to start")
        else:
            print("[AMBIENT] Audio recording is running...")
        
        # Capture schedule: wait, then capture
        # T-30: capture immediately (we're starting at T-30)
        # T-20: wait 10s, capture
        # T-10: wait 10s, capture  
        # T-0:  wait 10s, capture
        
        wait_times = [0, 10, 10, 10]  # Seconds to wait before each capture
        
        for i, wait_time in enumerate(wait_times):
            # Check for interrupt
            if check_interrupt():
                print("[AMBIENT] Interrupted by new message")
                self.cancel()
                return None
            
            if self._cancelled:
                return None
            
            # Wait
            if wait_time > 0:
                # Sleep in small increments to allow interrupt checking
                for _ in range(wait_time * 2):
                    if check_interrupt() or self._cancelled:
                        print("[AMBIENT] Interrupted during wait")
                        self.cancel()
                        return None
                    time.sleep(0.5)
            
            # Capture screenshot with label
            label = self.CAPTURE_LABELS[i] if i < len(self.CAPTURE_LABELS) else f"T-{i}"
            self.capture_screenshot(label)
        
        # Stop audio recording
        print("[AMBIENT] Stopping audio recording...")
        if audio_started:
            self.stop_audio()
        
        # Summary
        print(f"[AMBIENT] Capture complete:")
        print(f"  Screenshots: {len(self.data.screenshot_paths)}")
        for i, path in enumerate(self.data.screenshot_paths):
            label = self.data.screenshot_labels[i] if i < len(self.data.screenshot_labels) else "?"
            exists = "OK" if os.path.exists(path) else "MISSING"
            print(f"    [{i}] {label}: {path} ({exists})")
        print(f"  Audio: {self.data.audio_path or 'None'}")
        if self.data.audio_path:
            exists = "OK" if os.path.exists(self.data.audio_path) else "MISSING"
            print(f"    Status: {exists}")
        
        return self.data
    
    def get_data(self) -> AmbientData:
        """Get the current captured data."""
        return self.data
    
    def clear_data(self):
        """Clear captured data and temp files."""
        self.data.clear()


# Global instance for use across modules
_ambient_capture: Optional[AmbientCapture] = None


def get_ambient_capture() -> AmbientCapture:
    """Get or create the global AmbientCapture instance."""
    global _ambient_capture
    if _ambient_capture is None:
        _ambient_capture = AmbientCapture()
    return _ambient_capture
