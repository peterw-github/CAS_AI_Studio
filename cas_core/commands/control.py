"""
Control commands: freq, stop, prompt_now, help, ambient
"""

import cas_config as cfg
from cas_core.commands import register
from cas_core.protocol import CommandResult, TextResponse, serialize_responses
from cas_logic import templates
import threading
import cas_config as cfg



@register("freq", aliases=["frequency", "timer", "prompt_frequency"])
def handle_freq(args: str, context: dict) -> CommandResult:
    """Change the heartbeat frequency."""
    result = CommandResult()
    
    if not args:
        current = context.get('interval', cfg.DEFAULT_INTERVAL) // 60
        result.add_text(f"**[CAS]** Current frequency: {current} minutes.")
        return result
    
    try:
        minutes = int(args)
        
        # Validate range
        if minutes < 1:
            result.add_text("**[CAS ERROR]** Minimum frequency is 1 minute.")
            return result
        
        if minutes > 1440:  # 24 hours
            result.add_text("**[CAS ERROR]** Maximum frequency is 1440 minutes (24 hours).")
            return result
        
        # Set new interval
        result.new_interval = minutes * 60  # Convert to seconds
        result.add_text(f"**[CAS]** Frequency set to {minutes} minutes.")
        
        print(f"[CMD] Frequency changed to {minutes} minutes")
        
    except ValueError:
        result.add_text(f"**[CAS ERROR]** Invalid number: `{args}`")
    
    return result


@register("stop")
def handle_stop(args: str, context: dict) -> CommandResult:
    """Stop the CAS brain loop."""
    result = CommandResult()
    result.should_stop = True
    result.add_text("**[CAS]** Shutting down... Goodbye.")
    print("[CMD] Stop command received")
    return result


@register("prompt_now")
def handle_prompt_now(args: str, context: dict) -> CommandResult:
    """Trigger an immediate prompt."""
    result = CommandResult()
    # This is handled by the fact that we always respond to commands
    # The response itself acts as the "prompt"
    result.add_text("**[CAS]** Prompt triggered.")
    return result


@register("help")
def handle_help(args: str, context: dict) -> CommandResult:
    """Display the help file."""
    result = CommandResult()
    
    try:
        with open("commands_explained.md", "r", encoding="utf-8") as f:
            help_text = f.read()
        result.add_text(help_text)
    except FileNotFoundError:
        result.add_text("**[CAS ERROR]** Help file not found.")
    except Exception as e:
        result.add_text(f"**[CAS ERROR]** Failed to read help: {e}")
    
    return result


@register("ambient", aliases=["context", "ambient_mode"])
def handle_ambient(args: str, context: dict) -> CommandResult:
    """
    Toggle or control ambient capture mode.
    
    Usage:
        !CAS ambient        - Toggle on/off
        !CAS ambient on     - Enable
        !CAS ambient off    - Disable
        !CAS ambient status - Show current status
    """
    result = CommandResult()
    
    try:
        from cas_core.ambient import get_ambient_capture
        ambient = get_ambient_capture()
        
        args_lower = args.lower().strip() if args else ""
        
        if args_lower in ("on", "enable", "1", "true"):
            ambient.set_enabled(True)
            result.add_text("**[CAS]** Ambient mode **enabled**. "
                          "Screenshots and audio will be captured before each heartbeat.")
        
        elif args_lower in ("off", "disable", "0", "false"):
            ambient.set_enabled(False)
            result.add_text("**[CAS]** Ambient mode **disabled**. "
                          "Heartbeats will be text-only.")
        
        elif args_lower in ("status", "state", "?"):
            state = "enabled" if ambient.is_enabled() else "disabled"
            interval = context.get('interval', cfg.DEFAULT_INTERVAL)
            
            status_lines = [
                f"**[CAS AMBIENT STATUS]**",
                f"- Mode: **{state}**",
                f"- Heartbeat interval: {interval // 60} minutes",
            ]
            
            if ambient.is_enabled():
                if interval >= 30:
                    status_lines.append(f"- Captures: 4 screenshots + 30s audio per heartbeat")
                else:
                    status_lines.append(f"- ⚠️ Interval too short (<30s) - ambient capture skipped")
            
            result.add_text("\n".join(status_lines))
        
        else:
            # Toggle
            new_state = ambient.toggle()
            state_str = "enabled" if new_state else "disabled"
            result.add_text(f"**[CAS]** Ambient mode **{state_str}**.")
        
        print(f"[CMD] Ambient mode: {ambient.is_enabled()}")
        
    except ImportError as e:
        result.add_text(f"**[CAS ERROR]** Ambient module not available: {e}")
    
    return result


@register("break")
def handle_break(args: str, context: dict) -> CommandResult:
    """Set a break timer."""
    result = CommandResult()

    if not args:
        result.add_text("**[CAS]** Usage: `!CAS break <minutes>`")
        return result

    try:
        minutes = int(args)

        if minutes < 1:
            result.add_text("**[CAS ERROR]** Break must be at least 1 minute.")
            return result

        def send_break_reminder():
            from cas_logic.templates import format_break_over
            responses = [TextResponse(format_break_over())]
            with open(cfg.COMMAND_FILE, "w", encoding="utf-8") as f:
                f.write(serialize_responses(responses))
            print("[CAS] Break reminder sent.")

        timer = threading.Timer(minutes * 60, send_break_reminder)
        timer.daemon = True
        timer.start()

        result.add_text(f"**[CAS]** Break started. See you in {minutes} minute{'s' if minutes != 1 else ''}. Enjoy!")
        print(f"[CMD] Break timer set: {minutes} minutes")

    except ValueError:
        result.add_text(f"**[CAS ERROR]** Invalid number: `{args}`")

    return result