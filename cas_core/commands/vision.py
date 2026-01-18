"""
Vision commands: screenshot, screen_record, see, watch
"""

import cas_config as cfg
from cas_core.commands import register
from cas_core.protocol import CommandResult, Screenshot, ScreenRecord, PhonePhoto, PhoneVideo
from cas_core.adb import take_phone_snapshot, record_phone_video
from cas_logic.templates import format_screenshot_payload


@register("screenshot")
def handle_screenshot(args: str, context: dict) -> CommandResult:
    """Take a screenshot of the monitors."""
    result = CommandResult()
    
    print("[CMD] Taking screenshot...")
    interval_mins = context.get('interval', 600) // 60
    
    result.responses.append(Screenshot(
        message=format_screenshot_payload(interval_mins)
    ))
    
    return result


@register("screen_record")
def handle_screen_record(args: str, context: dict) -> CommandResult:
    """Record the screen using OBS."""
    result = CommandResult()
    
    duration = cfg.SCREEN_RECORDING_DURATION
    print(f"[CMD] Screen recording ({duration}s)...")
    
    # Import here to avoid circular dependency issues
    from cas_logic.screen_record import record_screen
    
    success = record_screen(duration)
    
    if success:
        result.responses.append(ScreenRecord(
            message=f"**[CAS RECORDING]**\nA screen recording ({duration}s) has been attached."
        ))
    else:
        result.add_text("**[CAS ERROR]** Recording failed. Is OBS open?")
    
    return result


@register("see")
def handle_see(args: str, context: dict) -> CommandResult:
    """Take a photo using the phone camera."""
    result = CommandResult()
    
    print("[CMD] Fetching phone camera snapshot...")
    
    success = take_phone_snapshot()
    
    if success:
        interval_mins = context.get('interval', 600) // 60
        result.responses.append(PhonePhoto(
            message=f"Phone Camera View (Captured at {interval_mins}m interval)."
        ))
    else:
        result.add_text("**[CAS ERROR]** Could not capture phone camera. Is IP Webcam running?")
    
    return result


@register("watch", aliases=["see_video", "record_eyes"])
def handle_watch(args: str, context: dict) -> CommandResult:
    """Record video using the phone camera."""
    result = CommandResult()
    
    print("[CMD] Recording phone video...")
    
    success = record_phone_video(duration_seconds=10)
    
    if success:
        result.responses.append(PhoneVideo(
            message="**[CAS VISION]**\nI am watching your feed. (Phone Video Captured)"
        ))
    else:
        result.add_text("**[CAS ERROR]** Could not retrieve vision feed from phone.")
    
    return result
