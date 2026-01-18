"""
Command parser for CAS.

Extracts !CAS commands from message text.
"""

import re
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ParsedCommand:
    """A single parsed command."""
    name: str           # Command name (lowercase)
    args: str           # Arguments (cleaned of quotes/backticks)
    raw_match: str      # Original matched text


def parse_commands(text: str) -> List[ParsedCommand]:
    """
    Extract all !CAS commands from message text.
    
    Matches patterns like:
        !CAS exec dir
        `!CAS screenshot`
        !CAS freq 15
    
    Returns list of ParsedCommand objects.
    """
    commands = []
    
    # Pattern: optional backtick, !CAS, command name, optional args, optional backtick
    pattern = r'(?m)^`?!CAS\s+(\w+)(?:\s+(.*?))?`?$'
    
    for match in re.finditer(pattern, text):
        name = match.group(1).lower()
        raw_args = match.group(2) if match.group(2) else ""
        
        # Clean arguments: remove backticks and quotes
        args = raw_args.strip().strip('`').strip('"').strip("'").strip()
        
        commands.append(ParsedCommand(
            name=name,
            args=args,
            raw_match=match.group(0)
        ))
    
    return commands


def has_commands(text: str) -> bool:
    """Quick check if text contains any !CAS commands."""
    return bool(re.search(r'(?m)^`?!CAS\s+\w+', text))
