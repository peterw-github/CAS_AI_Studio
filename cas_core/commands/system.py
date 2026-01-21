"""
System commands: exec, cd, upload_file, delete_file

Note: This is a placeholder. Replace with your existing system.py implementation.
"""

import os
import subprocess

import cas_config as cfg
from cas_core.commands import register
from cas_core.protocol import CommandResult, FileUpload, DeleteFile
from cas_logic import templates


def _get_cwd() -> str:
    """Get the current working directory."""
    if os.path.exists(cfg.CWD_FILE):
        with open(cfg.CWD_FILE, "r") as f:
            cwd = f.read().strip()
            if os.path.isdir(cwd):
                return cwd
    return cfg.AI_START_DIR


def _set_cwd(path: str):
    """Set the current working directory."""
    with open(cfg.CWD_FILE, "w") as f:
        f.write(path)


@register("exec")
def handle_exec(args: str, context: dict) -> CommandResult:
    """Execute a shell command."""
    result = CommandResult()
    
    if not args:
        result.add_text("**[CAS ERROR]** No command specified.")
        return result
    
    cwd = _get_cwd()
    
    try:
        proc = subprocess.run(
            args,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        output = proc.stdout + proc.stderr
        output = output.strip() if output else "(no output)"
        
        # Truncate if too long
        if len(output) > 2000:
            # Save to file
            filename = "exec_output.txt"
            filepath = os.path.join(cwd, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(output)
            result.add_text(templates.format_result_file(args[:30], filename))
            result.responses.append(FileUpload(
                path=filepath,
                message=""
            ))
        else:
            result.add_text(templates.format_result(args[:30], output))
        
    except subprocess.TimeoutExpired:
        result.add_text(templates.format_error(args[:30], "Command timed out (30s)"))
    except Exception as e:
        result.add_text(templates.format_error(args[:30], str(e)))
    
    return result


@register("cd")
def handle_cd(args: str, context: dict) -> CommandResult:
    """Change the working directory."""
    result = CommandResult()
    
    if not args:
        cwd = _get_cwd()
        result.add_text(f"**[CAS]** Current directory: `{cwd}`")
        return result
    
    # Handle relative paths
    if not os.path.isabs(args):
        args = os.path.join(_get_cwd(), args)
    
    args = os.path.normpath(args)
    
    if os.path.isdir(args):
        _set_cwd(args)
        result.add_text(templates.format_cd_success(args))
    else:
        result.add_text(templates.format_cd_error(args))
    
    return result


@register("upload_file", aliases=["upload"])
def handle_upload_file(args: str, context: dict) -> CommandResult:
    """Upload a file to the chat."""
    result = CommandResult()
    
    if not args:
        result.add_text("**[CAS ERROR]** No file specified.")
        return result
    
    # Handle relative paths
    if not os.path.isabs(args):
        args = os.path.join(_get_cwd(), args)
    
    if not os.path.exists(args):
        result.add_text(f"**[CAS ERROR]** File not found: `{args}`")
        return result
    
    filename = os.path.basename(args)
    result.responses.append(FileUpload(
        path=args,
        message=templates.format_upload_payload(filename)
    ))
    
    return result


@register("delete_file")
def handle_delete_file(args: str, context: dict) -> CommandResult:
    """Delete a file from the chat."""
    result = CommandResult()
    
    if not args:
        result.add_text("**[CAS ERROR]** No filename specified.")
        return result
    
    result.responses.append(DeleteFile(filename=args))
    result.add_text(templates.format_delete_success(args))
    
    return result
