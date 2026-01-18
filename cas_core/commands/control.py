"""
Control commands: freq, stop, prompt_now, help
"""

import os

from cas_core.commands import register
from cas_core.protocol import CommandResult
from cas_logic import templates


@register("freq", aliases=["frequency", "timer", "prompt_frequency"])
def handle_freq(args: str, context: dict) -> CommandResult:
    """Set the heartbeat frequency in minutes."""
    result = CommandResult()
    
    try:
        # Clean up the argument
        clean_args = args.replace("`", "").replace("[", "").replace("]", "").strip()
        minutes = int(clean_args)
        
        if minutes < 1:
            result.add_text(templates.format_freq_error_too_low())
            return result
        
        if minutes > 1440:  # 24 hours
            result.add_text(templates.format_freq_error_too_high())
            return result
        
        print(f"[CMD] Frequency set to {minutes}m")
        result.new_interval = minutes * 60
        result.add_text(templates.format_freq_confirm(minutes))
        
    except ValueError:
        print(f"[CMD ERROR] Invalid frequency: {args}")
        result.add_text(templates.format_freq_error_invalid(args))
    
    return result


@register("stop")
def handle_stop(args: str, context: dict) -> CommandResult:
    """Stop the CAS brain loop."""
    result = CommandResult()
    
    print("[CMD] Stop requested.")
    result.should_stop = True
    result.add_text(templates.format_stop_confirm())
    
    return result


@register("prompt_now")
def handle_prompt_now(args: str, context: dict) -> CommandResult:
    """Trigger an immediate prompt."""
    result = CommandResult()
    
    print("[CMD] Prompt now triggered.")
    interval_mins = context.get('interval', 600) // 60
    result.add_text(templates.format_prompt_now(interval_mins))
    
    return result


@register("help")
def handle_help(args: str, context: dict) -> CommandResult:
    """Display the command help file."""
    result = CommandResult()
    
    print("[CMD] Help requested.")
    
    # Try multiple possible locations for the help file
    possible_paths = [
        "commands_explained.md",
        os.path.join(os.path.dirname(__file__), "..", "..", "commands_explained.md"),
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    help_text = f.read()
                result.add_text(help_text)
                return result
            except Exception as e:
                result.add_text(templates.format_help_error_read(str(e)))
                return result
    
    result.add_text(templates.format_help_error_not_found())
    return result
