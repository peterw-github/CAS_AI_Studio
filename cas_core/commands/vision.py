"""
Vision commands: screenshot, screen_record, see, watch
"""

import cas_config as cfg
from cas_core.commands import register
from cas_core.protocol import CommandResult, Screenshot, ScreenRecord, PhonePhoto, PhoneVideo
from cas_logic import templates


@register("screenshot")
def handle_screenshot(args: str, context: dict) -> CommandResult:
    """Take a screenshot of the monitors."""
    result = CommandResult()
    
    print("[CMD] Taking screenshot...")
    
    result.responses.append(Screenshot(
        message=templates.format_screenshot_payload()
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
            message=templates.format_screen_record_payload(duration)
        ))
    else:
        result.add_text(templates.format_screen_record_error())
    
    return result


@register("see")
def handle_see(args: str, context: dict) -> CommandResult:
    """Take a photo using the phone camera."""
    result = CommandResult()
    
    print("[CMD] Fetching phone camera snapshot...")
    
    # Import here to avoid issues if adb module has missing dependencies
    from cas_core.adb import take_phone_snapshot
    
    success = take_phone_snapshot()
    
    if success:
        result.responses.append(PhonePhoto(
            message=templates.format_phone_photo_payload()
        ))
    else:
        result.add_text(templates.format_phone_photo_error())
    
    return result


@register("watch", aliases=["see_video", "record_eyes"])
def handle_watch(args: str, context: dict) -> CommandResult:
    """Record video using the phone camera."""
    result = CommandResult()
    
    print("[CMD] Recording phone video...")
    
    from cas_core.adb import record_phone_video
    
    success = record_phone_video(duration_seconds=10)
    
    if success:
        result.responses.append(PhoneVideo(
            message=templates.format_phone_video_payload()
        ))
    else:
        result.add_text(templates.format_phone_video_error())
    
    return result
