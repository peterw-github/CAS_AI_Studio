"""
Journal and memory logging for CAS.
"""

import os
import datetime
import cas_config as cfg


# File paths
JOURNAL_FILE = os.path.join(cfg.AI_START_DIR, "journal.md")
CRITICAL_FILE = os.path.join(cfg.AI_START_DIR, "critical_context.md")


def _append_to_file(filepath: str, content: str, header: str) -> tuple:
    """
    Append a timestamped entry to a file.
    Creates the file if it doesn't exist.
    
    Returns:
        (success: bool, message: str)
    """
    # Ensure directory exists
    folder = os.path.dirname(filepath)
    if folder and not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    formatted_entry = f"\n\n---\n**[{header}] {timestamp}**\n{content}\n"

    try:
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(formatted_entry)
        return True, f"Written to {os.path.basename(filepath)}"
    except Exception as e:
        return False, f"Error writing log: {e}"


def write_journal(content: str) -> tuple:
    """Write an entry to the journal file."""
    return _append_to_file(JOURNAL_FILE, content, "JOURNAL ENTRY")


def write_critical(content: str) -> tuple:
    """Write a critical memory entry."""
    return _append_to_file(CRITICAL_FILE, content, "CRITICAL MEMORY")
