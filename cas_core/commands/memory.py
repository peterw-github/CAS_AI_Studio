"""
Memory commands: log, remember
"""

from cas_core.commands import register
from cas_core.protocol import CommandResult
from cas_logic.logger import write_journal, write_critical


@register("log")
def handle_log(args: str, context: dict) -> CommandResult:
    """Write an entry to the journal."""
    result = CommandResult()
    
    if not args:
        result.add_text("**[CAS LOG ERROR]** Empty log message.")
        return result
    
    print("[CMD] Writing to journal...")
    success, msg = write_journal(args)
    result.add_text(f"**[CAS LOG]** {msg}")
    
    return result


@register("remember")
def handle_remember(args: str, context: dict) -> CommandResult:
    """Write a critical memory entry."""
    result = CommandResult()
    
    if not args:
        result.add_text("**[CAS MEMORY ERROR]** Empty memory content.")
        return result
    
    print("[CMD] Writing critical memory...")
    success, msg = write_critical(args)
    result.add_text(f"**[CAS MEMORY]** {msg}")
    
    return result
