"""
System commands: exec, cd, upload_file, delete_file
"""

import os
import subprocess
import time

import cas_config as cfg
from cas_core.commands import register
from cas_core.protocol import CommandResult, FileUpload, DeleteFile, TextResponse
from cas_logic import templates


# --- CWD STATE MANAGEMENT ---

def _get_cwd() -> str:
    """Get the current working directory (persisted across commands)."""
    if os.path.exists(cfg.CWD_FILE):
        try:
            with open(cfg.CWD_FILE, "r", encoding="utf-8") as f:
                path = f.read().strip()
                if os.path.isdir(path):
                    return path
        except:
            pass
    
    # Fallback to configured start dir
    if hasattr(cfg, 'AI_START_DIR') and os.path.isdir(cfg.AI_START_DIR):
        _set_cwd(cfg.AI_START_DIR)
        return cfg.AI_START_DIR
    
    return os.getcwd()


def _set_cwd(path: str):
    """Persist the current working directory."""
    with open(cfg.CWD_FILE, "w", encoding="utf-8") as f:
        f.write(path)


# --- CONFIGURATION ---
MAX_OUTPUT_CHARS = 2000


# --- COMMANDS ---

@register("exec")
def handle_exec(args: str, context: dict) -> CommandResult:
    """Execute a shell command."""
    result = CommandResult()
    
    if not args:
        result.add_text(templates.format_upload_error_no_file())
        return result
    
    print(f"[CMD] Executing: {args}")
    current_wd = _get_cwd()
    
    # Wrap command to capture the final CWD
    marker = "CAS_FOLDER_SYNC"
    wrapped_cmd = f'{args} && echo {marker} && cd'
    
    try:
        # Sanitize HTML entities
        cmd = args.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
        
        proc = subprocess.run(
            wrapped_cmd,
            shell=True,
            capture_output=True,
            text=True,
            cwd=current_wd,
            encoding='utf-8',
            errors='replace'
        )
        
        full_output = (proc.stdout + proc.stderr).strip()
        
        # Parse new CWD from output
        if marker in full_output:
            parts = full_output.split(marker)
            clean_output = parts[0].strip()
            new_path = parts[1].strip()
            
            if os.path.isdir(new_path):
                _set_cwd(new_path)
                status_tag = f"[cwd: {new_path}]"
            else:
                status_tag = f"[cwd: {current_wd}] (Path update failed)"
        else:
            clean_output = full_output
            status_tag = f"[cwd: {current_wd}]"
        
        # Safety valve: dump large outputs to file
        if len(clean_output) > MAX_OUTPUT_CHARS:
            filename = f"output_dump_{int(time.time())}.txt"
            with open(os.path.abspath(filename), "w", encoding="utf-8") as f:
                f.write(clean_output)
            output_text = f"[WARNING] Output too long. Saved to {filename}\n\n{status_tag}"
        else:
            output_text = f"{clean_output}\n\n{status_tag}" if clean_output else status_tag
        
        result.add_text(templates.format_result(args, output_text))
        
    except Exception as e:
        result.add_text(templates.format_result(args, f"Error: {e}"))
    
    return result


@register("cd")
def handle_cd(args: str, context: dict) -> CommandResult:
    """Change directory (alias for exec cd)."""
    return handle_exec(f"cd {args}", context)


@register("upload_file", aliases=["upload"])
def handle_upload(args: str, context: dict) -> CommandResult:
    """Upload a file to the chat."""
    result = CommandResult()
    
    if not args:
        result.add_text(templates.format_upload_error_no_file())
        return result
    
    # Resolve relative paths
    target_path = args
    if not os.path.isabs(target_path):
        target_path = os.path.join(_get_cwd(), target_path)
    
    if os.path.exists(target_path):
        print(f"[CMD] Uploading: {target_path}")
        filename = os.path.basename(target_path)
        
        result.responses.append(FileUpload(
            path=target_path,
            message=templates.format_upload_payload(filename)
        ))
    else:
        print(f"[CMD ERROR] File not found: {target_path}")
        result.add_text(templates.format_upload_error_not_found(args))
    
    return result


@register("delete_file")
def handle_delete_file(args: str, context: dict) -> CommandResult:
    """Delete a file from the chat by filename."""
    result = CommandResult()
    
    if not args:
        result.add_text(templates.format_delete_error_no_file())
        return result
    
    print(f"[CMD] Delete file: {args}")
    result.responses.append(DeleteFile(filename=args))
    result.add_text(templates.format_delete_confirm(args))
    
    return result
