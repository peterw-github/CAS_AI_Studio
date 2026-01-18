"""
Command registry for CAS.

Central dispatch for all !CAS commands.
"""

from typing import Dict, Callable, Optional
from cas_core.protocol import CommandResult


# Type alias for command handlers
# Signature: (args: str, context: dict) -> CommandResult
CommandHandler = Callable[[str, dict], CommandResult]

# Registry of all commands
_COMMANDS: Dict[str, CommandHandler] = {}

# Aliases (alternative names for commands)
_ALIASES: Dict[str, str] = {}


def register(name: str, aliases: list = None):
    """
    Decorator to register a command handler.
    
    Usage:
        @register("exec")
        def handle_exec(args: str, context: dict) -> CommandResult:
            ...
    """
    def decorator(func: CommandHandler):
        _COMMANDS[name] = func
        if aliases:
            for alias in aliases:
                _ALIASES[alias] = name
        return func
    return decorator


def dispatch(name: str, args: str, context: dict) -> Optional[CommandResult]:
    """
    Execute a command by name.
    
    Args:
        name: Command name (will be lowercased, aliases resolved)
        args: Command arguments
        context: Shared context dict (interval, etc.)
    
    Returns:
        CommandResult or None if command not found
    """
    from cas_logic import templates
    
    name = name.lower()
    
    # Resolve alias
    if name in _ALIASES:
        name = _ALIASES[name]
    
    # Find and execute handler
    if name in _COMMANDS:
        try:
            return _COMMANDS[name](args, context)
        except Exception as e:
            print(f"[COMMAND ERROR] {name}: {e}")
            result = CommandResult()
            result.add_text(templates.format_command_error(name, str(e)))
            return result
    
    return None


def list_commands() -> list:
    """Return list of all registered command names."""
    return list(_COMMANDS.keys())


def is_registered(name: str) -> bool:
    """Check if a command is registered."""
    name = name.lower()
    return name in _COMMANDS or name in _ALIASES


# --- IMPORT ALL COMMAND MODULES ---
# This triggers the @register decorators
from cas_core.commands import system
from cas_core.commands import vision
from cas_core.commands import memory
from cas_core.commands import control
