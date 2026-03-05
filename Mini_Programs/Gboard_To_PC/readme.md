# Voice Bridge (Gboard-to-CAS)

**Voice Bridge** is a lightweight Python tool that turns your smartphone into a hands-free voice interface for [CAS](../../CAS) (Custom AI Studio). Speak into your phone, say "send message", and your message is sent directly to the CAS Gemini session — no need to be at your computer.

## Features

- **Hands-Free Operation:** Dictate via Gboard voice typing on your phone, say "send message" to fire it off to CAS.
- **Direct CAS Integration:** Messages are sent directly to the CAS API — no clipboard middleman.
- **Auto-Config:** Reads session ID and API URL from `cas_config.json` automatically.
- **Zero-Install on Phone:** No app required; works entirely through the mobile browser.
- **Dark Mode UI:** Styled for OLED screens/night usage.

## How It Works

1. You open the Voice Bridge web page on your phone's browser.
2. Tap the textarea and use Gboard's microphone to dictate.
3. Say **"send message"** at the end of your dictation.
4. The trigger phrase is stripped, and the message is sent to your active CAS session via the API.
5. CAS processes the message, and the AI responds (with TTS if enabled).
6. The textarea clears, ready for your next message.

There's also a manual **Send to CAS** button as a fallback if you prefer tapping.

## Prerequisites

- **Computer:** Python 3 with a virtual environment.
- **Phone:** Chrome (or any modern browser) and Gboard (or any voice-to-text keyboard).
- **Network:** Both devices must be on the **same Wi-Fi network**.
- **CAS:** Must be running on the configured API URL (default: `http://localhost:3001`).

## Installation

1. **Create and activate the virtual environment** (if not already done):

       cd /mnt/slw_drive/Vaults/CAS_AI_Studio
       python3 -m venv .venv
       .venv/bin/pip install flask requests

2. **Ensure CAS config exists** at `/mnt/slw_drive/Vaults/CAS/cas_config.json` with a valid `system.session_id` and `paths.api_url`.

## Usage

### Option A: Double-click the desktop file

1. Open the project folder in Files.
2. Double-click `Voice Bridge.desktop` (right-click > "Allow Launching" if first time).

### Option B: Run from terminal

    bash run_gboard_server.sh

### Then on your phone:

1. The server prints a URL like `http://192.168.x.x:5000` — open it on your phone.
2. Tap the textarea, tap the Gboard microphone, and start speaking.
3. Say **"send message"** when done. Your message goes straight to CAS.

## Configuration

Voice Bridge reads its configuration from CAS:

- **Config file:** `/mnt/slw_drive/Vaults/CAS/cas_config.json`
- **Session ID:** `system.session_id` — the active CAS session to send messages to.
- **API URL:** `paths.api_url` — the CAS backend address.

The **trigger phrase** (`send message`) is defined in `gboard_server.py` as `TRIGGER_PHRASE`. The detection is case-insensitive and tolerates trailing punctuation.

The **debounce timer** is set to 1500ms — the trigger phrase is only checked 1.5 seconds after input stops, preventing premature sends while Gboard is still transcribing.

## Troubleshooting

**"Can't load the website on my phone"**

- **Firewall:** On Ubuntu, you may need to allow port 5000:

      sudo ufw allow 5000

- **IP Address:** If the printed IP doesn't work, run `ip addr` and look for your Wi-Fi adapter's IP.

**"send message" isn't triggering**

- Make sure Gboard actually typed the words "send message" in the textarea.
- The detection waits 1.5 seconds after the last input — give it a moment.
- Check that CAS is running and the session ID in `cas_config.json` is valid.

**"Error sending to CAS"**

- Verify CAS is running: `curl http://localhost:3001/api/sessions`
- Check that the session ID in `cas_config.json` matches an active session.

## License

Open source. Feel free to modify and hack away.
