"""
CAS Brain - Main orchestration loop.

This module is now much simpler - it just:
1. Manages the heartbeat schedule
2. Parses incoming commands
3. Dispatches commands to handlers
4. Sends responses back via the command queue
5. Bundles ambient captures (screenshots + audio) with heartbeats
"""

import time
import os
import importlib
# must also perform 'pip install tzdata'

import cas_config as cfg
from cas_core import (
    parse_commands,
    has_commands,
    dispatch,
    HeartbeatScheduler,
    read_latest_message,
    serialize_responses,
    CommandResult,
    TextResponse,
)
from cas_core.protocol import AmbientScreenshot, AmbientAudio, DeleteAllImages
from cas_logic.templates import format_heartbeat, format_ambient_heartbeat
from cas_logic.cas_voice import CASVoiceEngine



# Global voice instance
voice = None


def send_to_bridge(responses: list):
    """Write responses to the command queue file for the bridge to process."""
    with open(cfg.COMMAND_FILE, "w", encoding="utf-8") as f:
        f.write(serialize_responses(responses))
    time.sleep(0.2)


def build_ambient_responses(ambient_data) -> list:
    """
    Build response objects from ambient capture data.
    
    Returns list of AmbientScreenshot and AmbientAudio objects.
    """
    responses = []
    
    if not ambient_data:
        return responses
    
    # Add screenshots with their labels
    for i, screenshot_path in enumerate(ambient_data.screenshot_paths):
        if os.path.exists(screenshot_path):
            # Use stored label or fallback
            if i < len(ambient_data.screenshot_labels):
                label = ambient_data.screenshot_labels[i]
            else:
                label = f"Screenshot {i + 1}"
            
            responses.append(AmbientScreenshot(
                path=screenshot_path,
                label=label
            ))
    
    # Add audio
    if ambient_data.audio_path and os.path.exists(ambient_data.audio_path):
        # Calculate duration from file
        try:
            import wave
            with wave.open(ambient_data.audio_path, 'rb') as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                duration = frames / float(rate)
        except:
            duration = 30.0  # Fallback
        
        responses.append(AmbientAudio(
            path=ambient_data.audio_path,
            duration=duration
        ))
    
    return responses


def process_message(scheduler: HeartbeatScheduler) -> tuple:
    """
    Process the latest message from AI Studio.
    
    Returns:
        (new_interval, should_stop)
    """
    time.sleep(0.5)
    text = read_latest_message()
    
    # Voice output
    if voice:
        voice.speak(text)
    
    # Parse commands
    commands = parse_commands(text)
    
    if not commands:
        print("  >>> [INFO] No commands found (User/AI interaction).")
        return scheduler.interval, False
    
    # Build context for command handlers
    context = {
        'interval': scheduler.interval,
    }
    
    # Process each command
    all_responses = []
    new_interval = scheduler.interval
    should_stop = False
    
    for cmd in commands:
        print(f"  >>> [CMD] {cmd.name} {cmd.args[:50] if cmd.args else ''}")
        
        result = dispatch(cmd.name, cmd.args, context)
        
        if result:
            all_responses.extend(result.responses)
            
            if result.new_interval:
                new_interval = result.new_interval
                context['interval'] = new_interval  # Update for subsequent commands
            
            if result.should_stop:
                should_stop = True
    
    # Send responses
    if all_responses:
        # Add heartbeat footer (COMMENTED OUT, COMMANDS DON'T NEED TO TRIGGER HEARTBEAT MESSAGE, THAT IS ALREADY SCHEDULED ON ITS OWN)
        # heartbeat_text = format_heartbeat(new_interval // 60)
        # all_responses.append(TextResponse(heartbeat_text))

        send_to_bridge(all_responses)
        print("  >>> [RESPONSE SENT]")
    
    return new_interval, should_stop


def main():
    global voice
    
    print("[CAS BRAIN] Online. Initializing...")
    
    # Initialize voice engine
    voice = CASVoiceEngine()
    
    # Initialize scheduler
    scheduler = HeartbeatScheduler(cfg.DEFAULT_INTERVAL)

    # Track the last known config value so we only update when YOU change the file
    last_config_interval = cfg.DEFAULT_INTERVAL
    
    # Check ambient mode status
    try:
        from cas_core.ambient import get_ambient_capture
        ambient = get_ambient_capture()
        print(f"[CAS BRAIN] Ambient mode: {'ENABLED' if ambient.is_enabled() else 'disabled'}")
    except ImportError:
        print("[CAS BRAIN] Ambient mode: not available")
    
    # --- Startup Check ---
    # If there's a pending command from before we started, process it
    startup_text = read_latest_message()
    
    if has_commands(startup_text):
        print("[CAS BRAIN] Pending command detected at startup.")
        new_interval, should_stop = process_message(scheduler)
        
        if should_stop:
            return
        
        scheduler.set_interval(new_interval)
        scheduler.update_mtime()
    else:
        # No pending commands - adjust timing based on recent activity
        scheduler.adjust_for_recent_activity()
    
    # --- Main Loop ---
    while True:

        # --- NEW: HOT RELOAD CONFIG ---
        try:
            importlib.reload(cfg)
            # Only update scheduler if the file value actually changed
            if cfg.DEFAULT_INTERVAL != last_config_interval:
                print(f"[CAS BRAIN] Config change detected! Updating interval: {cfg.DEFAULT_INTERVAL}s")
                scheduler.set_interval(cfg.DEFAULT_INTERVAL)
                last_config_interval = cfg.DEFAULT_INTERVAL
        except Exception as e:
            print(f"[CAS BRAIN] Error reloading config: {e}")


        # Send heartbeat if due
        if scheduler.is_heartbeat_due():
            # Build heartbeat response
            responses = []
            
            # Check for ambient data
            if scheduler.has_ambient_data():
                ambient_data = scheduler.get_ambient_data()
                ambient_responses = build_ambient_responses(ambient_data)
                responses.extend(ambient_responses)
                
                # Use ambient-aware heartbeat text
                heartbeat = format_ambient_heartbeat(
                    scheduler.interval // 60,
                    len(ambient_data.screenshot_paths),
                    ambient_data.audio_path is not None
                )
                print(f"[CAS BRAIN] Heartbeat with ambient context: "
                      f"{len(ambient_data.screenshot_paths)} screenshots, "
                      f"audio={'yes' if ambient_data.audio_path else 'no'}")
            else:
                heartbeat = format_heartbeat(scheduler.interval // 60)
            
            responses.append(TextResponse(heartbeat))

            # 1. Send the Heartbeat (screenshots + audio)
            send_to_bridge(responses)
            print("[CAS BRAIN] Heartbeat sent.")

            # --- NEW AUTO-CLEANUP SEQUENCE ---
            print("[CAS BRAIN] Waiting for bridge to process heartbeat...")

            # 2. Safety Wait: Don't overwrite the queue until Bridge has cleared it
            # We give it up to 60 seconds to process the uploads
            timeout = 60
            while os.path.getsize(cfg.COMMAND_FILE) > 0 and timeout > 0:
                time.sleep(1)
                timeout -= 1

            if timeout > 0:
                # 3. User Requested Delay: Wait 5 seconds after processing is done
                print("[CAS BRAIN] Heartbeat processed. Waiting 5s before cleanup...")
                time.sleep(5)

                # 4. Send the Cleanup Command
                print("[CAS BRAIN] Sending auto-cleanup command...")
                send_to_bridge([DeleteAllImages()])
            else:
                print("[CAS BRAIN] Warning: Bridge took too long, skipping cleanup.")
            # ---------------------------------

            scheduler.schedule_next()
        
        # Wait (with interrupt detection and ambient capture)
        interrupted = scheduler.wait_for_next()
        
        if interrupted:
            new_interval, should_stop = process_message(scheduler)
            scheduler.update_mtime()
            
            if should_stop:
                break
            
            if new_interval != scheduler.interval:
                scheduler.set_interval(new_interval)
            else:
                # Even if interval didn't change, reschedule the heartbeat
                # This resets the timer after any AI response
                scheduler.schedule_next()
                print(f"[CAS BRAIN] Timer reset. Next heartbeat in {scheduler.interval // 60} minutes.")
    
    # Cleanup
    if voice:
        voice.shutdown()
    
    print("[CAS BRAIN] Shutdown complete.")


if __name__ == "__main__":
    main()
