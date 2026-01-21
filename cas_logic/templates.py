"""
Message templates for CAS.

All user-facing message strings are defined here for easy customization.
"""


def format_heartbeat(interval_minutes: int) -> str:
    """Format the standard heartbeat message."""
    return f"**[CAS HEARTBEAT]** Next pulse in {interval_minutes} minutes."


def format_ambient_heartbeat(interval_minutes: int, screenshot_count: int, has_audio: bool) -> str:
    """Format heartbeat with ambient context summary."""
    parts = []
    
    if screenshot_count > 0:
        parts.append(f"{screenshot_count} screenshots")
    
    if has_audio:
        parts.append("30s audio")
    
    context_str = " + ".join(parts) if parts else "no captures"
    
    return (
        f"**[CAS HEARTBEAT]** Ambient context attached ({context_str}). "
        f"Next pulse in {interval_minutes} minutes."
    )


def format_result(cmd: str, output: str) -> str:
    """Format command execution result."""
    return f"**[CAS RESULT: `{cmd}`]**\n```\n{output}\n```"


def format_result_file(cmd: str, filename: str) -> str:
    """Format command result when output was saved to file."""
    return f"**[CAS RESULT: `{cmd}`]** Output saved to `{filename}` (attached)."


def format_error(cmd: str, error: str) -> str:
    """Format command error message."""
    return f"**[CAS ERROR: `{cmd}`]** {error}"


def format_upload_payload(filename: str) -> str:
    """Format message for file upload."""
    return f"**[CAS FILE]** `{filename}` attached."


def format_screenshot_payload() -> str:
    """Format message for screenshot."""
    return "**[CAS SCREENSHOT]** Current screen captured."


def format_screen_record_payload(duration: int) -> str:
    """Format message for screen recording."""
    return f"**[CAS SCREEN RECORD]** {duration}s recording attached."


def format_screen_record_error() -> str:
    """Format error message for screen recording failure."""
    return "**[CAS ERROR]** Screen recording failed. Is OBS running with WebSocket enabled?"


def format_phone_photo_payload() -> str:
    """Format message for phone camera photo."""
    return "**[CAS VISION]** Phone camera snapshot attached."


def format_phone_photo_error() -> str:
    """Format error message for phone photo failure."""
    return "**[CAS ERROR]** Phone camera failed. Is IP Webcam running?"


def format_phone_video_payload() -> str:
    """Format message for phone camera video."""
    return "**[CAS VISION]** Phone camera video (10s) attached."


def format_phone_video_error() -> str:
    """Format error message for phone video failure."""
    return "**[CAS ERROR]** Phone video recording failed. Check ADB connection."


def format_log_success(entry: str) -> str:
    """Format confirmation for journal entry."""
    preview = entry[:50] + "..." if len(entry) > 50 else entry
    return f"**[CAS LOG]** Entry recorded: \"{preview}\""


def format_remember_success(content: str) -> str:
    """Format confirmation for critical memory."""
    preview = content[:50] + "..." if len(content) > 50 else content
    return f"**[CAS REMEMBER]** Stored: \"{preview}\""


def format_cd_success(new_dir: str) -> str:
    """Format confirmation for directory change."""
    return f"**[CAS]** Working directory: `{new_dir}`"


def format_cd_error(path: str) -> str:
    """Format error for directory change failure."""
    return f"**[CAS ERROR]** Directory not found: `{path}`"


def format_delete_success(filename: str) -> str:
    """Format confirmation for file deletion."""
    return f"**[CAS]** Deleted: `{filename}`"
