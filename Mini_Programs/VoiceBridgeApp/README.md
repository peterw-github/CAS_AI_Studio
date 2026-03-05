# Voice Bridge - Android App

Voice Bridge is a hands-free voice-to-CAS system. It uses an Android app to keep Gboard's microphone perpetually active via an AccessibilityService, and a Flask server on the PC to relay transcribed text to CAS (Custom AI Studio — a custom Gemini UI).

The phone is designed to be worn in a chest-mounted running belt (like Cortana from Halo), making screen interaction impractical. The entire system is designed for hands-free operation — you speak, say "send message", and your words are sent to CAS or copied to your PC's clipboard (toggled via an in-app switch).

## System Architecture

```
┌─────────────────────┐         HTTP POST          ┌─────────────────────┐
│   Android Phone     │  ───────────────────────>   │   PC (Ubuntu)       │
│   (Pixel 9)         │                             │                     │
│                     │   /send-to-cas              │   gboard_server.py  │
│  VoiceBridgeApp     │   /send-to-clipboard        │   (Flask, port 5000)│
│  + Gboard keyboard  │                             │         │           │
│  + AccessibilityService                           │    ┌────┴────┐      │
│                     │                             │    ▼         ▼      │
│                     │                             │  CAS API   PC      │
│                     │   audio/wav (if remote)     │  (localhost Clipboard│
│                     │  <───────────────────────   │   :3001)            │
│  MediaPlayer ◄──────│                             │     │               │
└─────────────────────┘                             │     ▼               │
                                                    │  VibeVoice TTS      │
                                                    │  (localhost:7860)   │
                                                    │     │               │
                                                    │     ▼               │
                                                    │  AudioFiles/*.wav   │
                                                    └─────────────────────┘
```

Both devices must be on the same Wi-Fi network (or connected via ngrok for remote use).

## How It Works

1. User opens VoiceBridgeApp on phone, taps **Start Listening** once.
2. App opens the Gboard keyboard, double-taps the mic button via AccessibilityService.
3. Gboard transcribes speech into the app's text field with full punctuation.
4. Every 2 seconds, the app polls Gboard's accessibility tree to check mic state.
5. If the mic has timed out (Gboard's `VoiceDictationButton` shows "Use voice typing"), the app double-taps to restart it.
6. When the user says **"send message"**, the trigger phrase is stripped and the text is POSTed to the Flask server.
7. Depending on the **Clipboard toggle** in the app:
   - **Toggle OFF** (default): Sends to `/send-to-cas` → Flask forwards to CAS via `POST /api/chat/stream` → CAS responds (with TTS if enabled).
   - **Toggle ON**: Sends to `/send-to-clipboard` → Flask copies the text to the PC's clipboard via `pyperclip`.
8. If `remote_audio` is enabled in `cas_config.json`, the Flask server waits for CAS + TTS to finish, then returns the generated WAV audio in the HTTP response. The app detects the `audio/wav` content type, saves it to a temp file, and plays it via Android's `MediaPlayer`.
9. The text field clears and listening continues.

## Why Gboard (Not SpeechRecognizer API)

Android's `SpeechRecognizer` API was tried first but produces lower-quality transcriptions — notably missing punctuation. Gboard's voice typing uses Google's production speech-to-text pipeline and includes automatic punctuation, capitalization, and better accuracy. The AccessibilityService approach lets us use Gboard's quality while automating the mic restart that Gboard doesn't natively support.

## Why Double-Tap

A single tap on Gboard's mic button gives ~6-10 seconds of listening before timeout. A double-tap activates a longer listening mode (~60 seconds). Combined with the 2-second polling that auto-restarts the mic, this provides near-continuous voice input.

## Components

### 1. Android App (`VoiceBridgeApp/`)

The native Android app that controls Gboard's microphone.

| File | Purpose |
|------|---------|
| `app/src/main/java/com/voicebridge/app/MainActivity.kt` | Main activity — UI, mic polling, trigger detection, HTTP sending |
| `app/src/main/java/com/voicebridge/app/GboardAccessibilityService.kt` | AccessibilityService — mic state detection, double-tap gestures |
| `app/src/main/res/layout/activity_main.xml` | UI layout — dark theme, compact for use with keyboard open |
| `app/src/main/res/xml/accessibility_service_config.xml` | Accessibility service configuration |
| `app/src/main/AndroidManifest.xml` | App manifest — permissions, service declaration |
| `app/build.gradle.kts` | App module build config |
| `build.gradle.kts` | Root project build config (AGP 8.7.3, Kotlin 2.0.21) |
| `settings.gradle.kts` | Gradle settings |

### 2. Flask Server (`../Gboard_To_PC/`)

The PC-side relay server that receives text from the phone and forwards to CAS.

| File | Purpose |
|------|---------|
| `gboard_server.py` | Flask server — `/send-to-cas` and `/send-to-clipboard` endpoints |
| `run_gboard_server.sh` | Shell launcher script |
| `ngrok` | ngrok binary for remote access tunneling |
| `Voice Bridge.desktop` | GNOME desktop file for launching Flask server |
| `Voice Bridge Remote.desktop` | GNOME desktop file for launching ngrok tunnel (also at `~/Desktop/`) |

---

## Android App Details

### MainActivity.kt

Core logic:

- **Settings persistence**: Server URL, mic coordinates, and clipboard toggle state saved to `SharedPreferences`.
- **Start Listening flow**: Focuses transcript `EditText` → shows keyboard → waits 1.5s → double-taps mic coordinates → starts polling.
- **Mic polling**: Every 2 seconds, calls `GboardAccessibilityService.isMicActive()`. If `false`, double-taps mic to restart.
- **Trigger detection**: `TextWatcher` on the transcript `EditText` with 1.5-second debounce. Regex: `send\s*message[.!?,\s]*$` (case-insensitive).
- **Clipboard/CAS toggle**: `SwitchMaterial` toggle determines send destination. OFF = `/send-to-cas` (CAS mode), ON = `/send-to-clipboard` (clipboard mode). State persisted in SharedPreferences.
- **Send message**: POSTs plain text to the appropriate Flask endpoint via OkHttp. When `remote_audio` is enabled on the server, the response contains a WAV file which is saved to cache and played via `MediaPlayer`.
- **Audio playback**: Detects `Content-Type: audio/*` in HTTP response. Saves audio bytes to a temp file (`tts_response.wav` in cache dir), plays via Android's built-in `MediaPlayer`. OkHttp read timeout is 120 seconds to accommodate TTS generation time.
- **Screen stays on**: `FLAG_KEEP_SCREEN_ON` prevents the screen from sleeping.

Key constants:
```
DEFAULT_SERVER_URL = "http://192.168.0.51:5000"
MIC_POLL_INTERVAL_MS = 2000
Trigger phrase regex: send\s*message[.!?,\s]*$ (case-insensitive)
Debounce: 1500ms
```

### GboardAccessibilityService.kt

Two responsibilities:

**1. Mic state detection** (`checkMicState` / `findMicState`):
- Iterates all accessible windows via `windows` property.
- Finds the Gboard window (package: `com.google.android.inputmethod.latin`).
- Recursively walks the accessibility tree looking for the `VoiceDictationButton` node.
- Content description `"Stop voice typing"` → mic is ON.
- Content description `"Use voice typing"` → mic is OFF.
- Returns `null` if Gboard window not found.

**2. Double-tap gesture** (`tapAtCoordinates`):
- Creates two `StrokeDescription` objects: one at t=0ms (50ms duration), one at t=150ms (50ms duration).
- Both strokes tap the same (x, y) coordinates.
- Dispatched via `dispatchGesture`.

Critical accessibility service config flags:
```xml
android:canPerformGestures="true"           <!-- Required for dispatchGesture -->
android:canRetrieveWindowContent="true"     <!-- Required for reading Gboard's tree -->
android:accessibilityFlags="flagRetrieveInteractiveWindows"  <!-- Required to see Gboard's window -->
```

Without `canPerformGestures`, taps silently fail. Without `flagRetrieveInteractiveWindows`, `windows` only returns the app's own window, not Gboard's.

### Layout (activity_main.xml)

Top-to-bottom layout order:
1. "Voice Bridge" title
2. Server URL input
3. Mic X / Y coordinate inputs
4. A11y status (green ON / red OFF) + connection status
5. **Clipboard/CAS toggle** — "Mode: Send to CAS" (white) or "Mode: Clipboard" (blue)
6. **Transcript text area** (ScrollView with EditText, fills remaining space)
7. Start/Stop Listening button (green)
8. "Say 'send message' when done" hint
9. A11y Settings button (gray) + Clear button (pink)

Uses `fitsSystemWindows="true"` to avoid overlap with Android's status bar. All buttons use `textAllCaps="false"` and `app:backgroundTint` (Material Components namespace).

### Build Configuration

- **AGP**: 8.7.3
- **Kotlin**: 2.0.21
- **Gradle**: 8.9
- **Compile SDK**: 35 (Android 15)
- **Min SDK**: 28 (Android 9)
- **Target SDK**: 35
- **JVM Target**: 17

Dependencies:
- `androidx.appcompat:appcompat:1.7.0`
- `com.google.android.material:material:1.12.0`
- `com.squareup.okhttp3:okhttp:4.12.0`

---

## Flask Server Details

### gboard_server.py

- Reads CAS config from `/mnt/slw_drive/Vaults/CAS/cas_config.json` at startup.
- Extracts `paths.api_url` (default: `http://localhost:3001`) and `system.session_id`.
- Reads `tts.remote_audio` to determine audio delivery mode.
- Serves an HTML page at `/` (legacy web-based voice input — still functional but superseded by the Android app).
- Two POST endpoints:
  - `POST /send-to-cas` — accepts plain UTF-8 text. Behavior depends on `remote_audio`:
    - **`remote_audio: false`** (default): Fire-and-forget — forwards to CAS in a background thread, returns `200 OK` immediately.
    - **`remote_audio: true`**: Synchronous — sends to CAS, waits for the full response stream to complete, then polls `AudioFiles/` for a new WAV file (with size-stability check to avoid serving partial files). Returns the WAV with `Content-Type: audio/wav`. Times out after 90 seconds if no audio appears.
  - `POST /send-to-clipboard` — accepts plain UTF-8 text, copies to PC clipboard via `pyperclip`.
- Auto-detects LAN IP via UDP socket trick (`connect("8.8.8.8", 80)` then `getsockname()`).
- Runs on `0.0.0.0:5000`.

### CAS Config Structure

The server reads `/mnt/slw_drive/Vaults/CAS/cas_config.json`:
```json
{
  "system": {
    "session_id": "<UUID of active CAS session>"
  },
  "paths": {
    "api_url": "http://localhost:3001",
    "audio_output": "AudioFiles"
  },
  "tts": {
    "remote_audio": false
  }
}
```

---

## Setup Guide

### Prerequisites

- **Phone**: Google Pixel 9 (or any Android 9+ device with Gboard)
- **PC**: Ubuntu 24.04 LTS with CAS running
- **Network**: Both devices on the same Wi-Fi
- **Tools**: Android Studio (snap), ADB, Python 3 venv

### 1. PC Setup (Flask Server)

```bash
# Create venv (if not already done)
cd /mnt/slw_drive/Vaults/CAS_AI_Studio
python3 -m venv .venv
.venv/bin/pip install flask requests pyperclip

# Run the server
cd Mini_Programs/Gboard_To_PC
bash run_gboard_server.sh
# Note the IP address printed (e.g., http://192.168.0.100:5000)
```

Or double-click `Voice Bridge.desktop` in GNOME Files.

### 2. Android App Build & Install

```bash
cd /mnt/slw_drive/Vaults/CAS_AI_Studio/Mini_Programs/VoiceBridgeApp

# Set environment
export JAVA_HOME=/snap/android-studio/209/jbr
export ANDROID_HOME=/home/john/Android/Sdk
export PATH="$PATH:$ANDROID_HOME/platform-tools"

# Connect phone via USB (USB debugging must be enabled)
adb devices  # Should show device

# Build and install
./gradlew installDebug
```

### 3. Phone Setup

1. Open **Voice Bridge** app.
2. Tap **A11y Settings** → find "Voice Bridge" → enable the accessibility service.
3. Set the **Server URL** to the Flask server's IP (e.g., `http://192.168.0.100:5000`).
4. Set **Mic X** and **Mic Y** to the screen coordinates of Gboard's microphone button.
   - To find coordinates: enable Developer Options → "Pointer location" → tap the mic button and note the X/Y values shown at the top of the screen.
5. Tap **Start Listening**. The keyboard opens, mic activates, and you're hands-free.

### 4. Finding Mic Coordinates

1. Go to phone Settings → Developer options → enable "Pointer location".
2. Open any app with a text field and bring up Gboard.
3. Tap the microphone button on Gboard.
4. Note the X and Y coordinates displayed at the top of the screen.
5. Enter these into the Voice Bridge app.
6. Disable "Pointer location" when done.

### 5. Remote Access (ngrok)

To use Voice Bridge away from your local network:

1. Set `"remote_audio": true` in `cas_config.json` (so audio plays on phone instead of PC).
2. Restart the Flask server (it reads config at startup).
3. Start ngrok to expose the Flask server:
   ```bash
   ngrok http 5000
   ```
4. Copy the ngrok URL (e.g., `https://xxxx-xx-xx.ngrok-free.app`).
5. In the Voice Bridge app, change **Server URL** to the ngrok URL.
6. Disconnect from Wi-Fi — it works over mobile data.

When done, set `"remote_audio": false` to go back to PC audio playback.

---

## Troubleshooting

### "A11y: OFF" shown in red
The accessibility service isn't enabled. Tap "A11y Settings" and enable "Voice Bridge".

### Mic doesn't auto-restart
- Verify mic coordinates are correct (see "Finding Mic Coordinates" above).
- Check logcat for `VoiceBridgeA11y` tag: `adb logcat -s VoiceBridgeA11y`.
- Ensure Gboard is the active keyboard.

### "Send failed" error
- Verify Flask server is running on PC.
- Verify phone and PC are on the same network.
- Check the server URL in the app matches the IP printed by the server.
- If using HTTP (not HTTPS), `usesCleartextTraffic="true"` is already set in the manifest.

### "send message" trigger not firing
- Gboard must actually type the words "send message" — check the transcript.
- The trigger has a 1.5-second debounce; wait a moment after speaking.
- The regex is case-insensitive and tolerates trailing punctuation (periods, commas, etc.).

### ADB can't find device
- Enable USB debugging on phone: Settings → Developer options → USB debugging.
- Ensure udev rule exists: `/etc/udev/rules.d/51-android.rules` with Google vendor ID `18d1`.
- Run `sudo udevadm control --reload-rules && sudo udevadm trigger`.
- Reconnect USB cable and tap "Allow" on phone.

### Taps not working (dispatchGesture returns true but nothing happens)
This was a critical issue during development. The fix was adding `android:canPerformGestures="true"` to `accessibility_service_config.xml`. If you modify this file, you must **disable and re-enable** the accessibility service in phone settings for changes to take effect.

### Can only see app's own window in accessibility tree
Must have `android:accessibilityFlags="flagRetrieveInteractiveWindows"` in the accessibility service config, and use the `windows` property (not `rootInActiveWindow`) to iterate all windows.

### Remote audio not playing on phone
- Verify `"remote_audio": true` is set in `cas_config.json` and the Flask server was restarted after the change.
- Check the Flask server startup log — it should print `[Config] Remote audio ENABLED — will serve audio from: /mnt/slw_drive/Vaults/CAS/AudioFiles`.
- Verify VibeVoice TTS is running on the PC (localhost:7860) and CAS TTS is enabled.
- Check Flask server logs for `[Audio] Serving:` (success) or `[Audio] Timed out` (TTS didn't generate in time).
- Check `adb logcat -s VoiceBridge` for `Audio save/play error` or `MediaPlayer error` on the phone side.

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Gboard over SpeechRecognizer API | Gboard provides punctuation, capitalization, and higher quality transcription |
| AccessibilityService for mic control | Only way to programmatically tap Gboard's mic button without root |
| Double-tap instead of single-tap | Extends Gboard mic timeout from ~10s to ~60s |
| 2-second polling interval | Fast enough to catch mic timeouts, slow enough to not drain battery |
| Fire-and-forget CAS integration (local) | CAS has TTS that talks back on PC speakers; no need to wait for or display the response |
| Synchronous + audio return (remote) | When away from PC, Flask waits for TTS to finish and returns WAV in the HTTP response so the phone can play it |
| File polling for audio delivery | speak_response.py saves WAV to AudioFiles/; Flask polls for new files rather than requiring IPC. Simple, decoupled, no new dependencies |
| Clipboard toggle | Sometimes you want voice text in the clipboard (for pasting anywhere) instead of sending to CAS |
| Flask server as relay | CAS API runs on localhost; phone can't reach it directly. Also handles clipboard access on PC |
| Coordinate-based tapping | Gboard's mic button isn't reliably clickable via accessibility node actions; coordinate tapping via dispatchGesture is more reliable |
| SharedPreferences for settings | Simple persistence for server URL and mic coordinates across app restarts |

## Development Notes

### Building from Command Line

The `gradlew` wrapper and `gradle-wrapper.jar` must be present. If missing:
```bash
# Copy from Gradle cache
cp ~/.gradle/caches/8.9/transforms/*/transformed/unzipped-distribution/gradle-8.9/gradle/wrapper/gradle-wrapper.jar gradle/wrapper/
```

### Debugging

```bash
# All Voice Bridge logs
adb logcat -s VoiceBridge VoiceBridgeA11y

# Mic state polling
adb logcat -s VoiceBridge | grep "Mic poll"

# Tap events
adb logcat -s VoiceBridgeA11y | grep "tap"
```
