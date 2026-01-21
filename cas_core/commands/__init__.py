"""
Command registry and dispatch for CAS.

Commands are registered using the @register decorator.
"""

from typing import Callable, Dict, List, Optional
from cas_core.protocol import CommandResult


# Command registry: name -> handler function
_commands: Dict[str, Callable] = {}
_aliases: Dict[str, str] = {}  # alias -> canonical name


def register(name: str, aliases: List[str] = None):
    """
    Decorator to register a command handler.
    
    Usage:
        @register("mycommand", aliases=["mc", "mycmd"])
        def handle_mycommand(args: str, context: dict) -> CommandResult:
            ...
    """
    def decorator(func: Callable):
        _commands[name.lower()] = func
        
        if aliases:
            for alias in aliases:
                _aliases[alias.lower()] = name.lower()
        
        return func
    
    return decorator


def dispatch(name: str, args: str, context: dict) -> Optional[CommandResult]:
    """
    Dispatch a command to its handler.
    
    Args:
        name: Command name (case-insensitive)
        args: Command arguments
        context: Context dict with interval, etc.
    
    Returns:
        CommandResult from handler, or None if command not found
    """
    name_lower = name.lower()
    
    # Check aliases
    if name_lower in _aliases:
        name_lower = _aliases[name_lower]
    
    # Find handler
    handler = _commands.get(name_lower)
    
    if handler is None:
        print(f"[DISPATCH] Unknown command: {name}")
        result = CommandResult()
        result.add_text(f"**[CAS ERROR]** Unknown command: `{name}`")
        return result
    
    try:
        return handler(args, context)
    except Exception as e:
        print(f"[DISPATCH] Error in {name}: {e}")
        result = CommandResult()
        result.add_text(f"**[CAS ERROR]** Command `{name}` failed: {e}")
        return result


def list_commands() -> List[str]:
    """Return list of registered command names."""
    return list(_commands.keys())


def is_registered(name: str) -> bool:
    """Check if a command is registered."""
    name_lower = name.lower()
    return name_lower in _commands or name_lower in _aliases


# Import command modules to trigger registration
# These imports must happen AFTER the register function is defined
from cas_core.commands import system
from cas_core.commands import vision
from cas_core.commands import memory
from cas_core.commands import control
