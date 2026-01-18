"""
CAS Brain - Main orchestration loop.

This module is now much simpler - it just:
1. Manages the heartbeat schedule
2. Parses incoming commands
3. Dispatches commands to handlers
4. Sends responses back via the command queue
"""

import time
import os

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
from cas_logic.templates import format_heartbeat
from cas_logic.cas_voice import CASVoiceEngine


# Global voice instance
voice = None


def send_to_bridge(responses: list):
    """Write responses to the command queue file for the bridge to process."""
    with open(cfg.COMMAND_FILE, "w", encoding="utf-8") as f:
        f.write(serialize_responses(responses))
    time.sleep(0.2)


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
        # Add heartbeat footer
        heartbeat_text = format_heartbeat(new_interval // 60)
        all_responses.append(TextResponse(heartbeat_text))
        
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
        # Send heartbeat if due
        if scheduler.is_heartbeat_due():
            heartbeat = format_heartbeat(scheduler.interval // 60)
            send_to_bridge([TextResponse(heartbeat)])
            print("[CAS BRAIN] Heartbeat sent.")
            scheduler.schedule_next()
        
        # Wait (with interrupt detection)
        interrupted = scheduler.wait_for_next()
        
        if interrupted:
            new_interval, should_stop = process_message(scheduler)
            scheduler.update_mtime()
            
            if should_stop:
                break
            
            if new_interval != scheduler.interval:
                scheduler.set_interval(new_interval)
    
    # Cleanup
    if voice:
        voice.shutdown()
    
    print("[CAS BRAIN] Shutdown complete.")


if __name__ == "__main__":
    main()
