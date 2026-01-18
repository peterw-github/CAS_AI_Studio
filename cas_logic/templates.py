"""
Message templates for CAS responses.

ALL user-facing messages are defined here for easy customization.
"""

import datetime
from textwrap import dedent


def get_timestamp() -> str:
    """Get current timestamp in ISO format."""
    return datetime.datetime.now().isoformat(timespec='minutes')


# =============================================================================
# HEARTBEAT & CORE
# =============================================================================

def format_heartbeat(interval_minutes: int) -> str:
    return dedent(f"""
        **[CAS HEARTBEAT]**
        `Time: {get_timestamp()}`
        `Current Prompt Frequency: {interval_minutes} minutes`
        `!CAS help` for available features.
    """).strip()


# =============================================================================
# SYSTEM COMMANDS (exec, cd, upload, delete)
# =============================================================================

def format_result(cmd: str, output: str) -> str:
    """Command execution result."""
    return dedent(f"""
        **[CAS RESULT]**
        `CMD: {cmd}`
        ```
        {output}
        ```
    """).strip()


def format_upload_payload(filename: str) -> str:
    return f"**[CAS UPLOAD]** File `{filename}` attached."


def format_upload_error_not_found(path: str) -> str:
    return f"**[CAS ERROR]** File not found: `{path}`"


def format_upload_error_no_file() -> str:
    return "**[CAS ERROR]** No filename specified."


def format_delete_confirm(filename: str) -> str:
    return f"**[CAS DELETE]** Removed `{filename}` from conversation."


def format_delete_error_no_file() -> str:
    return "**[CAS ERROR]** No filename specified for deletion."


# =============================================================================
# VISION COMMANDS (screenshot, screen_record, see, watch)
# =============================================================================

def format_screenshot_payload() -> str:
    return "**[CAS VISION]** Screenshot attached."


def format_screen_record_payload(duration: int) -> str:
    return f"**[CAS RECORDING]** Screen recording ({duration}s) attached."


def format_screen_record_error() -> str:
    return "**[CAS ERROR]** Recording failed. Is OBS open?"


def format_phone_photo_payload() -> str:
    return "**[CAS EYES]** Phone camera snapshot attached."


def format_phone_photo_error() -> str:
    return "**[CAS ERROR]** Could not capture phone camera. Is IP Webcam running?"


def format_phone_video_payload() -> str:
    return "**[CAS EYES]** Phone video attached."


def format_phone_video_error() -> str:
    return "**[CAS ERROR]** Could not retrieve video from phone."


# =============================================================================
# MEMORY COMMANDS (log, remember)
# =============================================================================

def format_log_success(detail: str) -> str:
    return f"**[CAS LOG]** {detail}"


def format_log_error_empty() -> str:
    return "**[CAS ERROR]** Empty log message."


def format_remember_success(detail: str) -> str:
    return f"**[CAS MEMORY]** {detail}"


def format_remember_error_empty() -> str:
    return "**[CAS ERROR]** Empty memory content."


# =============================================================================
# CONTROL COMMANDS (freq, stop, prompt_now, help)
# =============================================================================

def format_freq_confirm(interval_minutes: int) -> str:
    return f"**[CAS SYSTEM]** Frequency updated to {interval_minutes} minutes."


def format_freq_error_invalid(value: str) -> str:
    return f"**[CAS ERROR]** Invalid frequency value: `{value}`"


def format_freq_error_too_low() -> str:
    return "**[CAS ERROR]** Frequency must be at least 1 minute."


def format_freq_error_too_high() -> str:
    return "**[CAS ERROR]** Frequency cannot exceed 1440 minutes (24 hours)."


def format_stop_confirm() -> str:
    return "**[CAS SYSTEM]** Shutting down..."


def format_prompt_now(interval_minutes: int) -> str:
    return dedent(f"""
        **[CAS PROMPT]**
        `Time: {get_timestamp()}`
        `Current Prompt Frequency: {interval_minutes} minutes`
        
        You triggered `!CAS prompt_now`. You're welcome to think about anything you want, and reply however you want.
    """).strip()


def format_help_error_not_found() -> str:
    return "**[CAS ERROR]** Help file not found."


def format_help_error_read(error: str) -> str:
    return f"**[CAS ERROR]** Could not read help file: {error}"


# =============================================================================
# GENERIC ERRORS
# =============================================================================

def format_command_error(cmd: str, error: str) -> str:
    return f"**[CAS ERROR]** `{cmd}` failed: {error}"
