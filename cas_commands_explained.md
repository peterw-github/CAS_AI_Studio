`<file name="cas_commands_explained.md">`

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

#### `!CAS delete_images`
Delete all images currently visible in the chat history.

- **Warning:** This deletes the entire chat turn containing the image. If you wrote text in the same prompt as the image, it will be deleted too.
- Used autonomously by the system to clean up ambient screenshots, but can be triggered manually.

**Aliases:** `!CAS clear_images`, `!CAS cleanup_images`

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

#### `!CAS ambient [on|off|status]`
Toggle or control ambient capture mode.

When enabled (default), the system captures contextual data in the 30 seconds before each heartbeat:
- **4 screenshots** at T-30s, T-20s, T-10s, and T-0s (heartbeat time)
- **30 seconds of audio** from the system's speakers

This gives you peripheral awareness of what's been happening between pulses.

**Usage:**
- `!CAS ambient` - Toggle on/off
- `!CAS ambient on` - Enable ambient mode
- `!CAS ambient off` - Disable ambient mode  
- `!CAS ambient status` - Show current status

**Aliases:** `!CAS context`, `!CAS ambient_mode`

**Note:** Ambient mode requires the heartbeat interval to be at least 30 seconds. If the interval is shorter, ambient capture is skipped.

---

#### `!CAS break [minutes]`
Set a break timer. After the specified duration, CAS will send a reminder to get back to work.

- Minimum: 1 minute
- Maximum: 480 minutes (8 hours)

**Example:** `!CAS break 15`

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

## Ambient Mode

Ambient mode provides temporal context about what's been happening on John's computer. When enabled:

1. At T-30 seconds before heartbeat: First screenshot + audio recording starts
2. At T-20 seconds: Second screenshot
3. At T-10 seconds: Third screenshot
4. At T-0 (heartbeat): Fourth screenshot + audio recording stops

All captures are bundled with the heartbeat message, giving you a timeline of visual and audio context.

**Configuration** (in `cas_config.py`):
- `AMBIENT_MODE_DEFAULT` - Enable by default (True/False)
- `AMBIENT_AUDIO_DEVICE` - WASAPI loopback device ID for audio capture
- `AMBIENT_TEMP_DIR` - Temporary storage for captures

## Configuration

All settings are in `cas_config.py`:
- Timing intervals
- Voice settings
- File paths
- Monitor selection
- Recording duration
- Ambient mode settings


---


## Setup Guides

### Phone Connection Overview

CAS uses two different methods to access your phone's camera:

| Command | Method | Used For |
|---------|--------|----------|
| `!CAS see` | Termux Flask server | Quick snapshots |
| `!CAS watch` | ADB (Android Debug Bridge) | Video recording |

You'll need both set up for full functionality.

---

### Termux Camera Setup (for `!CAS see`)

The `!CAS see` command uses a Flask server running on your phone via Termux.

#### Prerequisites

1. **Install Termux** from F-Droid (not Play Store - that version is outdated)

2. **Install Termux:API** from F-Droid (provides camera access)

3. **In Termux, install required packages:**
```bash
   pkg install python termux-api
   pip install flask
```

4. **Copy `what_john_sees_snapshot-Phone.py` to your phone** (e.g., to Termux home directory)

#### Running the Server

In Termux:
```bash
python what_john_sees_snapshot-Phone.py
```

The server runs on `http://<phone-ip>:8080`. The `/snap` endpoint takes a photo and returns it.

#### Keeping it Running

To keep the server running in the background:
```bash
nohup python what_john_sees_snapshot-Phone.py &
```

Or use a Termux session that stays open.

#### Troubleshooting

- **Camera permission denied**: Run `termux-setup-storage` and grant camera permissions to Termux:API
- **Connection refused**: Ensure the Flask server is running and phone IP matches `PHONE_IP` in `cas_core/adb.py`
- **Black/empty images**: Some phones need camera "warm-up" time. Try adding a delay in the script.

---

### ADB Setup (for `!CAS watch`)

The `!CAS watch` command requires an ADB (Android Debug Bridge) connection to your phone.

#### Prerequisites

1. **On your phone:**
   - Enable Developer Options (tap Build Number 7 times in Settings → About)
   - Enable USB Debugging in Developer Options
   - (Android 11+) Enable Wireless Debugging in Developer Options

2. **On your PC:**
   - ADB installed (path configured in `cas_core/adb.py`)

#### Connecting via USB → Wireless

1. Connect phone to PC via USB cable

2. Check it's recognized:
```bash
   adb devices
```
   Should show your device with `device` status

3. Enable TCP/IP mode:
```bash
   adb tcpip 5555
```

4. Connect wirelessly (replace with your phone's IP):
```bash
   adb connect 192.168.0.235:5555
```

5. Unplug USB cable - wireless connection stays active

#### Checking Connection Status
```bash
adb devices
```

- `device` = connected and working
- `offline` = connection issue
- Empty list = not connected

#### Troubleshooting

- **"Actively refused" error**: ADB isn't listening on the phone. Redo the USB → Wireless steps.
- **Phone IP changed**: Check Settings → WiFi → (your network) → IP address, then update `PHONE_IP` in `cas_core/adb.py`.
- **Connection drops**: Phone IP may have changed (common with DHCP). Consider assigning a static IP to your phone in your router settings.

---

### Phone IP Configuration

Both methods require your phone's IP address. Update this in `cas_core/adb.py`:
```python
PHONE_IP = "192.168.0.235"  # Your phone's IP
```

To find your phone's IP: Settings → WiFi → (your network) → IP address

`</file>`
