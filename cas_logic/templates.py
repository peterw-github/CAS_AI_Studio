"""
Message templates for CAS responses.
"""

import datetime
from textwrap import dedent


def get_timestamp() -> str:
    """Get current timestamp in ISO format."""
    return datetime.datetime.now().isoformat(timespec='minutes')


def format_heartbeat(interval_minutes: int) -> str:
    """Format a heartbeat message."""
    return dedent(f"""
        **[CAS HEARTBEAT]**
        `Time: {get_timestamp()}`
        `Current Prompt Frequency: {interval_minutes} minutes`
        `!CAS help` for available features.
    """).strip()


def format_screenshot_payload(interval_minutes: int) -> str:
    """Format a screenshot attachment message."""
    return dedent("""
        **[CAS VISION]**
        A screenshot has been attached, that shows what is currently on all three monitors.
    """).strip()


def format_upload_payload(filename: str, interval_minutes: int) -> str:
    """Format a file upload message."""
    return dedent(f"""
        **[CAS UPLOAD]**
        File `{filename}` has been attached as requested.
    """).strip()


def format_result(cmd: str, output: str) -> str:
    """Format a command execution result."""
    return dedent(f"""
        **[CAS RESULT]**
        `CMD: {cmd}`
        ```
        {output}
        ```
    """).strip()


def format_freq_confirm(interval_minutes: int) -> str:
    """Format a frequency change confirmation."""
    return dedent(f"""
        **[CAS SYSTEM]**
        Frequency updated to {interval_minutes} minutes.
    """).strip()


def format_prompt_now(interval_minutes: int) -> str:
    """Format a prompt_now response."""
    return dedent(f"""
        **[CAS PROMPT]**
        `Time: {get_timestamp()}`
        `Current Prompt Frequency: {interval_minutes} minutes`
        
        **Message:**
        You triggered `!CAS prompt_now`. You're welcome to think about anything you want, and reply however you want. Your attention mechanism can put a bit of its focus on your message just before this prompt, to get a better idea of why you triggered this command.
    """).strip()
