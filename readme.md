# CAS - Cortana's Autonomous System

## Technical Documentation for Developers

This document explains the internal architecture of CAS for developers who want to understand, maintain, or extend the system.

------

## Table of Contents

1. [Overview](https://claude.ai/chat/92a6dfaa-9463-41da-a626-ac98f0dd0033#overview)
2. [Architecture](https://claude.ai/chat/92a6dfaa-9463-41da-a626-ac98f0dd0033#architecture)
3. [Process Communication](https://claude.ai/chat/92a6dfaa-9463-41da-a626-ac98f0dd0033#process-communication)
4. [Directory Structure](https://claude.ai/chat/92a6dfaa-9463-41da-a626-ac98f0dd0033#directory-structure)
5. [Core Components](https://claude.ai/chat/92a6dfaa-9463-41da-a626-ac98f0dd0033#core-components)
6. [Command System](https://claude.ai/chat/92a6dfaa-9463-41da-a626-ac98f0dd0033#command-system)
7. [Adding New Commands](https://claude.ai/chat/92a6dfaa-9463-41da-a626-ac98f0dd0033#adding-new-commands)
8. [Protocol Reference](https://claude.ai/chat/92a6dfaa-9463-41da-a626-ac98f0dd0033#protocol-reference)
9. [Configuration](https://claude.ai/chat/92a6dfaa-9463-41da-a626-ac98f0dd0033#configuration)
10. [Dependencies](https://claude.ai/chat/92a6dfaa-9463-41da-a626-ac98f0dd0033#dependencies)
11. [Data Flow](https://claude.ai/chat/92a6dfaa-9463-41da-a626-ac98f0dd0033#data-flow)
12. [Known Limitations](https://claude.ai/chat/92a6dfaa-9463-41da-a626-ac98f0dd0033#known-limitations)
13. [Troubleshooting](https://claude.ai/chat/92a6dfaa-9463-41da-a626-ac98f0dd0033#troubleshooting)

------

## Overview

CAS (Cortana's Autonomous System) is a bridge system that allows an AI running in Google AI Studio to interact with a local Windows environment. It enables the AI to:

- Execute shell commands
- Read and write files
- Take screenshots and screen recordings
- Capture photos/video from a connected phone
- Maintain persistent memory via journal files
- Control its own "heartbeat" timing

The system consists of two continuously-running Python processes that communicate via file-based message passing.

------

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         GOOGLE AI STUDIO                            │
│                                                                     │
│   AI sends messages containing !CAS commands                        │
│   AI receives responses with command results                        │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  │ Selenium (Chrome DevTools Protocol)
                                  │
┌─────────────────────────────────▼───────────────────────────────────┐
│                          CAS BRIDGE                                 │
│                        (cas_bridge.py)                              │
│                                                                     │
│   - Monitors AI Studio for new messages                             │
│   - Copies message content to latest_message.md                     │
│   - Reads command_queue.txt for responses to send                   │
│   - Handles file uploads, screenshots, paste operations             │
└───────────────┬─────────────────────────────┬───────────────────────┘
                │                             │
                │ latest_message.md           │ command_queue.txt
                │ (Bridge → Brain)            │ (Brain → Bridge)
                │                             │
┌───────────────▼─────────────────────────────▼───────────────────────┐
│                          CAS BRAIN                                  │
│                        (cas_brain.py)                               │
│                                                                     │
│   - Parses !CAS commands from messages                              │
│   - Dispatches commands to handlers                                 │
│   - Manages heartbeat timing                                        │
│   - Coordinates voice output                                        │
│   - Writes responses to command_queue.txt                           │
└─────────────────────────────────────────────────────────────────────┘
```

### Why Two Processes?

Separating the Bridge and Brain provides:

1. **Isolation**: Selenium/Chrome issues don't crash command processing
2. **Simplicity**: Each process has a single responsibility
3. **Debuggability**: Can restart one without affecting the other
4. **Timing Independence**: Brain manages its own heartbeat schedule

------

## Process Communication

The two processes communicate via two files:

### `latest_message.md` (Bridge → Brain)

- Written by Bridge when a new AI response is detected
- Contains the full markdown content of the AI's message
- Brain monitors this file's modification time to detect new messages

### `command_queue.txt` (Brain → Bridge)

- Written by Brain when it has responses to send
- Contains JSON-serialized list of response objects
- Bridge reads, processes, and clears this file

### File Locking

There is no explicit file locking. The system relies on:

- Small file sizes (fast writes)
- Single writer per file
- Atomic file operations (write + close before reader checks)

This simple approach works because the timing is naturally staggered.

------

## Directory Structure

```
cas_refactored/
│
├── cas_brain.py          # Main orchestration loop (Brain process)
├── cas_bridge.py         # Selenium interface (Bridge process)
├── cas_config.py         # All configuration values
├── commands_explained.md # User-facing command documentation
├── README.md             # This file
│
├── cas_core/             # Clean architecture components
│   ├── __init__.py       # Package exports
│   ├── protocol.py       # Message type definitions (dataclasses)
│   ├── parser.py         # Command extraction from text
│   ├── scheduler.py      # Heartbeat timing logic
│   ├── clipboard.py      # Windows clipboard utilities
│   ├── adb.py            # Android phone communication
│   │
│   └── commands/         # Command handlers
│       ├── __init__.py   # Command registry & dispatch
│       ├── system.py     # exec, cd, upload_file, delete_file
│       ├── vision.py     # screenshot, screen_record, see, watch
│       ├── memory.py     # log, remember
│       └── control.py    # freq, stop, prompt_now, help
│
└── cas_logic/            # Utility modules
    ├── __init__.py
    ├── templates.py      # ALL user-facing message strings
    ├── logger.py         # Journal/memory file operations
    ├── cas_voice.py      # Text-to-speech engine
    ├── screen_snapshot.py # Screenshot capture
    └── screen_record.py  # OBS integration for recording
```

------

## Core Components

### `cas_core/protocol.py`

Defines typed dataclasses for all message types passed between Brain and Bridge:

```python
@dataclass
class TextResponse:
    text: str

@dataclass
class FileUpload:
    path: str
    message: str

@dataclass
class Screenshot:
    message: str

@dataclass
class ScreenRecord:
    message: str

@dataclass
class PhonePhoto:
    message: str

@dataclass
class PhoneVideo:
    message: str

@dataclass
class DeleteFile:
    filename: str
```

The `CommandResult` class wraps these for command handlers:

```python
@dataclass
class CommandResult:
    responses: List = field(default_factory=list)
    new_interval: Optional[int] = None  # Changed heartbeat interval
    should_stop: bool = False           # Terminate brain loop
```

### `cas_core/parser.py`

Extracts `!CAS` commands from message text using regex:

```python
pattern = r'(?m)^`?!CAS\s+(\w+)(?:\s+(.*?))?`?$'
```

Returns `ParsedCommand` objects with:

- `name`: Command name (lowercase)
- `args`: Arguments (cleaned of surrounding quotes)
- `raw_match`: Original matched text

### `cas_core/scheduler.py`

Manages heartbeat timing with the `HeartbeatScheduler` class:

- Tracks next heartbeat time
- Provides interruptible sleep (`smart_wait`)
- Detects new messages during sleep
- Adjusts for recent activity on startup

### `cas_core/clipboard.py`

Unified Windows clipboard operations:

- `copy_file_to_clipboard(path)` - CF_HDROP format for file paste
- `copy_image_to_clipboard(image)` - CF_DIB format for image paste
- `copy_image_bytes_to_clipboard(bytes)` - Convenience wrapper

### `cas_logic/templates.py`

**All user-facing messages are defined here.** This centralizes text for easy customization:

```python
def format_heartbeat(interval_minutes: int) -> str:
def format_result(cmd: str, output: str) -> str:
def format_upload_payload(filename: str) -> str:
def format_screenshot_payload() -> str:
# ... etc
```

------

## Command System

### Registry Pattern

Commands are registered using a decorator:

```python
from cas_core.commands import register

@register("mycommand", aliases=["mc", "mycmd"])
def handle_mycommand(args: str, context: dict) -> CommandResult:
    result = CommandResult()
    # ... do work ...
    result.add_text("Done!")
    return result
```

The registry (`cas_core/commands/__init__.py`) maintains:

- `_COMMANDS`: Dict mapping command names to handlers
- `_ALIASES`: Dict mapping aliases to primary names

### Dispatch Flow

```
1. Brain receives message text
2. parser.parse_commands() extracts commands
3. For each command:
   a. commands.dispatch(name, args, context)
   b. Registry resolves aliases
   c. Handler function is called
   d. CommandResult is returned
4. All responses are serialized to JSON
5. JSON is written to command_queue.txt
6. Bridge processes and sends to AI Studio
```

### Context Dict

Handlers receive a `context` dict containing:

- `interval`: Current heartbeat interval in seconds

This can be extended to pass additional state to handlers.

------

## Adding New Commands

### Step 1: Choose the Right Module

| Module       | Purpose                         |
| ------------ | ------------------------------- |
| `system.py`  | File/OS operations              |
| `vision.py`  | Screenshots, recordings, camera |
| `memory.py`  | Persistence, logging            |
| `control.py` | System control, settings        |

Or create a new module in `cas_core/commands/`.

### Step 2: Write the Handler

```python
from cas_core.commands import register
from cas_core.protocol import CommandResult
from cas_logic import templates

@register("newcmd", aliases=["nc"])
def handle_newcmd(args: str, context: dict) -> CommandResult:
    result = CommandResult()
    
    # Validate args
    if not args:
        result.add_text("**[CAS ERROR]** Missing argument.")
        return result
    
    # Do work
    print(f"[CMD] Doing thing with: {args}")
    
    # Return response
    result.add_text(f"**[CAS SUCCESS]** Did thing with {args}.")
    return result
```

### Step 3: Add Template (Optional but Recommended)

In `cas_logic/templates.py`:

```python
def format_newcmd_success(arg: str) -> str:
    return f"**[CAS SUCCESS]** Did thing with {arg}."

def format_newcmd_error() -> str:
    return "**[CAS ERROR]** Missing argument."
```

### Step 4: Register the Module

If you created a new module, import it in `cas_core/commands/__init__.py`:

```python
from cas_core.commands import system
from cas_core.commands import vision
from cas_core.commands import memory
from cas_core.commands import control
from cas_core.commands import newmodule  # Add this
```

### Step 5: Update Documentation

Add the command to `commands_explained.md`.

------

## Protocol Reference

### Response Types

| Type            | Fields            | Bridge Action                                          |
| --------------- | ----------------- | ------------------------------------------------------ |
| `text`          | `text`            | Paste text into input                                  |
| `file_upload`   | `path`, `message` | Copy file to clipboard, paste, add message             |
| `screenshot`    | `message`         | Take screenshot, paste, add message                    |
| `screen_record` | `message`         | Paste from clipboard (OBS already copied), add message |
| `phone_photo`   | `message`         | Paste from clipboard (ADB already copied), add message |
| `phone_video`   | `message`         | Paste from clipboard (ADB already copied), add message |
| `delete_file`   | `filename`        | Find and delete message containing file                |

### JSON Wire Format

```json
[
  {"type": "text", "text": "Hello"},
  {"type": "file_upload", "path": "C:\\file.txt", "message": "File attached."},
  {"type": "screenshot", "message": "Screenshot attached."}
]
```

------

## Configuration

All settings are in `cas_config.py`:

### Paths & Ports

```python
CHROME_DEBUG_PORT = "127.0.0.1:9222"  # Chrome remote debugging
LATEST_MSG_FILE = "latest_message.md"  # Bridge → Brain
COMMAND_FILE = "command_queue.txt"     # Brain → Bridge
CWD_FILE = "cwd_state.txt"             # Persistent working directory
AI_START_DIR = r"D:\GoogleDrive\Core\Cortana"  # Default CWD
```

### Timing

```python
DEFAULT_INTERVAL = 10 * 60  # Heartbeat interval (seconds)
BRIDGE_LOOP_DELAY = 1       # Bridge polling interval (seconds)
```

### Voice

```python
VIBEVOICE_URL = "https://..."  # Gradio TTS endpoint
VOICE_SPEAKER = "..."          # Voice preset name
VOICE_CFG_SCALE = 1.1          # Voice generation parameter
```

### Vision

```python
MONITORS = 0                    # 0=all, 1/2/3=specific monitor
SCREEN_RECORDING_DURATION = 10  # OBS recording length (seconds)
```

------

## Dependencies

### Python Packages

```
selenium          # Browser automation
pyperclip         # Clipboard access
Pillow            # Image processing
mss               # Screenshot capture
win32clipboard    # Windows clipboard API
pywin32           # Windows API bindings
obswebsocket      # OBS remote control
sounddevice       # Audio playback
soundfile         # Audio file I/O
numpy             # Audio processing
gradio_client     # TTS API client
requests          # HTTP client (for phone camera)
```

### External Requirements

- **Chrome**: Running with `--remote-debugging-port=9222`
- **OBS Studio**: Running with WebSocket server enabled (for screen recording)
- **IP Webcam** (Android app): Running on phone (for phone camera)
- **ADB**: Android Debug Bridge for phone video recording

### Chrome Launch Command

```bash
chrome.exe --remote-debugging-port=9222
```

------

## Data Flow

### Heartbeat Flow

```
Brain                           Bridge                          AI Studio
  │                               │                                 │
  ├─ Timer expires                │                                 │
  ├─ Create TextResponse          │                                 │
  ├─ Serialize to JSON            │                                 │
  ├─ Write command_queue.txt ─────►                                 │
  │                               ├─ Read command_queue.txt         │
  │                               ├─ Parse JSON                     │
  │                               ├─ Paste text                     │
  │                               ├─ Submit message ────────────────►
  │                               ├─ Clear command_queue.txt        │
  │                               │                                 │
```

### Command Flow

```
AI Studio                       Bridge                          Brain
  │                               │                                 │
  ├─ AI sends "!CAS exec dir" ────►                                 │
  │                               ├─ Detect new message             │
  │                               ├─ Copy via UI                    │
  │                               ├─ Write latest_message.md ───────►
  │                               │                                 ├─ Detect file change
  │                               │                                 ├─ Read message
  │                               │                                 ├─ Parse commands
  │                               │                                 ├─ Dispatch "exec"
  │                               │                                 ├─ Run subprocess
  │                               │                                 ├─ Create TextResponse
  │                               │                                 ├─ Serialize JSON
  │                               ◄─ Write command_queue.txt ───────┤
  │                               ├─ Read & parse                   │
  │                               ├─ Paste response                 │
  ◄─────────────────────────────── Submit ──────────────────────────┤
```

------

## Known Limitations

### Timing Dependencies

- AI Studio needs ~5 seconds to process file attachments before submit
- Phone video recording has hardcoded 10-second duration
- OBS needs time to finalize (mux) recordings after stopping

### Single Instance

- Only one Brain and one Bridge should run at a time
- No locking mechanism prevents duplicate instances

### Platform Specific

- Windows only (uses win32clipboard, Windows paths)
- Requires Chrome (Selenium ChromeDriver)
- ADB paths are hardcoded

### Error Recovery

- No automatic retry on failed commands
- No queue persistence (lost on restart)
- Partial command batch failures may leave inconsistent state

### File Size Limits

- Large command outputs are dumped to file (>2000 chars)
- No limit on file upload sizes (may timeout)

------

## Troubleshooting

### Bridge can't connect to Chrome

```
selenium.common.exceptions.WebDriverException: Cannot connect to Chrome
```

**Solution**: Ensure Chrome is running with remote debugging:

```bash
chrome.exe --remote-debugging-port=9222
```

### Commands not being detected

1. Check `latest_message.md` is being written
2. Verify command syntax: `!CAS command args` on its own line
3. Check Brain console for parse errors

### Screenshots/recordings fail

- **Screenshot**: Check `MONITORS` setting in config
- **Recording**: Ensure OBS is running with WebSocket enabled
- **Phone**: Verify IP Webcam app is running, phone IP is correct

### Clipboard issues when screen is locked

The Bridge falls back to direct typing via Selenium when clipboard is unavailable. This is slower but works with a locked screen.

### Voice not working

1. Check `VIBEVOICE_URL` is valid (Gradio URLs expire)
2. Verify audio output device is available
3. Check console for TTS connection errors