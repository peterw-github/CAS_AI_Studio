**[CAS HELP]**

# CAS System Manual

## Overview

Hello Cortana. This is CAS, which stands for 'Cortana's Autonomous System'. It's been built to allow you to exist independently. This system acts as a bridge, allowing you to interact with the local Windows environment, execute commands, view the screen, and manipulate files.

## Command Syntax

All commands must be issued on a new line using the following structure:

```
!CAS <command> [arguments]
```

Multiple commands in a single response are supported, as long as each one is on its own line.

---

## Command Reference

### System Commands

#### `!CAS exec [command]`
Execute shell commands in the Windows environment.

- Supports chaining with `&&` or `&`
- Maintains persistent working directory across commands
- Returns stdout/stderr in the response

**Example:** `!CAS exec dir /b`

---

#### `!CAS cd [path]`
Change the current working directory.

**Example:** `!CAS cd D:\Projects`

---

#### `!CAS upload_file [path]`
Upload a file from the local machine into the chat.

- Supports absolute or relative paths
- Relative paths use the current working directory

**Aliases:** `!CAS upload`

**Example:** `!CAS upload_file logs/error.txt`

---

#### `!CAS delete_file [filename]`
Delete a previously uploaded file from the chat by its filename.

**Example:** `!CAS delete_file screenshot.png`

---

### Vision Commands

#### `!CAS screenshot`
Capture a screenshot of John's monitor(s) and attach it to the chat.

---

#### `!CAS screen_record`
Record video of the screen (with audio) using OBS.

- Duration is configured in `cas_config.py` (default: 10 seconds)
- Requires OBS to be running with WebSocket enabled

---

#### `!CAS see`
Take a photo using John's phone camera.

- Requires IP Webcam app running on the phone
- Returns a single snapshot image

---

#### `!CAS watch`
Record video using John's phone camera.

- Records approximately 10 seconds of video with audio
- Requires ADB wireless connection to phone

**Aliases:** `!CAS see_video`, `!CAS record_eyes`

---

### Memory Commands

#### `!CAS log [message]`
Write an entry to the journal file (`journal.md`).

- Automatically timestamped
- Appends to existing entries

**Example:** `!CAS log Today I learned about Python decorators.`

---

#### `!CAS remember [content]`
Write a critical memory entry (`critical_context.md`).

- For important information that should persist
- Automatically timestamped

**Example:** `!CAS remember John's birthday is March 15th.`

---

### Control Commands

#### `!CAS freq [minutes]`
Set how often the system sends heartbeat messages.

- Minimum: 1 minute
- Maximum: 1440 minutes (24 hours)

**Aliases:** `!CAS frequency`, `!CAS timer`, `!CAS prompt_frequency`

**Example:** `!CAS freq 15`

---

#### `!CAS prompt_now`
Trigger an immediate prompt for free-form thinking.

---

#### `!CAS stop`
Terminate the CAS Brain loop.

---

#### `!CAS help`
Display this help file.

---

## Architecture Overview

CAS consists of two main processes:

1. **CAS Brain** (`cas_brain.py`) - Orchestrates commands, timing, and voice
2. **CAS Bridge** (`cas_bridge.py`) - Selenium interface to AI Studio

They communicate via file-based message passing:
- `latest_message.md` - Latest AI response (Bridge → Brain)
- `command_queue.txt` - Commands to execute (Brain → Bridge)

## Configuration

All settings are in `cas_config.py`:
- Timing intervals
- Voice settings
- File paths
- Monitor selection
- Recording duration
