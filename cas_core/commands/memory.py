"""
Memory commands: log, remember

Note: This is a placeholder. Replace with your existing memory.py implementation.
"""

import os
import datetime

from cas_core.commands import register
from cas_core.protocol import CommandResult
from cas_logic import templates


# File paths for memory
JOURNAL_FILE = "journal.md"
CRITICAL_FILE = "critical_context.md"


def _append_to_file(filepath: str, content: str):
    """Append timestamped content to a file."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(f"\n## {timestamp}\n\n{content}\n")


@register("log")
def handle_log(args: str, context: dict) -> CommandResult:
    """Write an entry to the journal."""
    result = CommandResult()
    
    if not args:
        result.add_text("**[CAS ERROR]** No message to log.")
        return result
    
    try:
        _append_to_file(JOURNAL_FILE, args)
        result.add_text(templates.format_log_success(args))
    except Exception as e:
        result.add_text(f"**[CAS ERROR]** Failed to log: {e}")
    
    return result


@register("remember")
def handle_remember(args: str, context: dict) -> CommandResult:
    """Write a critical memory entry."""
    result = CommandResult()
    
    if not args:
        result.add_text("**[CAS ERROR]** No content to remember.")
        return result
    
    try:
        _append_to_file(CRITICAL_FILE, args)
        result.add_text(templates.format_remember_success(args))
    except Exception as e:
        result.add_text(f"**[CAS ERROR]** Failed to remember: {e}")
    
    return result
