import json
import logging
import threading
import os
import time
import glob
import pyperclip
from flask import Flask, request, render_template_string, send_file
import requests as http_requests

# Disable standard Flask logging to keep the console clean
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)

# Load CAS config
CAS_CONFIG_PATH = "/mnt/slw_drive/Vaults/CAS/cas_config.json"
with open(CAS_CONFIG_PATH) as f:
    cas_config = json.load(f)

CAS_API_URL = cas_config["paths"]["api_url"]
CAS_SESSION_ID = cas_config["system"]["session_id"]
TRIGGER_PHRASE = "send message"

# Remote audio settings
REMOTE_AUDIO = cas_config.get("tts", {}).get("remote_audio", False)
AUDIO_FILES_DIR = os.path.join(
    os.path.dirname(CAS_CONFIG_PATH),
    cas_config.get("paths", {}).get("audio_output", "AudioFiles")
)

if REMOTE_AUDIO:
    print(f"[Config] Remote audio ENABLED — will serve audio from: {AUDIO_FILES_DIR}")
else:
    print(f"[Config] Remote audio disabled — fire-and-forget mode")


def send_to_cas_async(message):
    """Send message to CAS in a background thread (fire and forget)."""
    def _stream():
        try:
            sid = CAS_SESSION_ID
            resp = http_requests.post(
                f"{CAS_API_URL}/api/chat/stream",
                json={"sessionId": sid, "message": message},
                stream=True,
                timeout=120
            )
            # Consume the stream so CAS processes the full response
            for _ in resp.iter_lines():
                pass
        except Exception as e:
            print(f"\n[CAS Error]: {e}")
    threading.Thread(target=_stream, daemon=True).start()


def send_to_cas_sync(message):
    """Send message to CAS and wait for completion (blocking)."""
    resp = http_requests.post(
        f"{CAS_API_URL}/api/chat/stream",
        json={"sessionId": CAS_SESSION_ID, "message": message},
        stream=True,
        timeout=120
    )
    # Consume the full stream so CAS processes the response
    for _ in resp.iter_lines():
        pass


def wait_for_new_audio(since_time, timeout=90, poll_interval=1.0):
    """Poll AudioFiles/ for a WAV file newer than since_time.

    Returns the file path, or None if timed out.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            files = glob.glob(os.path.join(AUDIO_FILES_DIR, "tts_*.wav"))
            for f in sorted(files, key=os.path.getmtime, reverse=True):
                if os.path.getmtime(f) >= since_time:
                    # Verify file is complete (not being written to)
                    size1 = os.path.getsize(f)
                    time.sleep(0.3)
                    size2 = os.path.getsize(f)
                    if size1 == size2 and size1 > 0:
                        return f
                break  # Only check the newest file
        except OSError:
            pass
        time.sleep(poll_interval)
    return None


# The HTML interface for your phone
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Voice Bridge</title>
    <style>
        body { font-family: sans-serif; padding: 20px; background: #121212; color: #e0e0e0; }
        textarea {
            width: 100%; height: 250px;
            font-size: 18px; padding: 10px;
            background: #1e1e1e; color: #fff;
            border: 1px solid #333; border-radius: 8px;
            box-sizing: border-box;
        }
        .status { margin-top: 10px; color: #00ff00; font-size: 14px; margin-bottom: 10px; }
        .hint { color: #888; font-size: 13px; margin-bottom: 15px; }
        button {
            width: 100%;
            padding: 15px;
            font-size: 18px;
            border: none;
            border-radius: 8px;
            font-weight: bold;
            cursor: pointer;
            margin-bottom: 10px;
        }
        #sendBtn { background-color: #4CAF50; color: #fff; }
        #sendBtn:active { background-color: #388E3C; }
        #clearBtn { background-color: #CF6679; color: #000; }
        #clearBtn:active { background-color: #b00020; }
    </style>
</head>
<body>
    <h3>🎙️ Voice to CAS</h3>
    <textarea id="textbox" placeholder="Tap microphone on Gboard and speak..."></textarea>
    <div id="status" class="status">Ready</div>
    <div class="hint">Say "<strong>send message</strong>" when done, or tap Send.</div>

    <button id="sendBtn">Send to CAS</button>
    <button id="clearBtn">Clear Text</button>

    <script>
        const textbox = document.getElementById('textbox');
        const status = document.getElementById('status');
        const sendBtn = document.getElementById('sendBtn');
        const clearBtn = document.getElementById('clearBtn');
        let timeout = null;

        const TRIGGER = /send\\s*message[.!?,\\s]*$/i;

        function sendToCAS(text) {
            if (!text.trim()) return;
            status.innerText = "Sending to CAS...";
            fetch('/send-to-cas', {
                method: 'POST',
                headers: {'Content-Type': 'text/plain'},
                body: text.trim()
            })
            .then(response => {
                if (response.ok) {
                    status.innerText = "Sent to CAS!";
                    textbox.value = "";
                    textbox.focus();
                } else {
                    status.innerText = "Error sending to CAS";
                }
            })
            .catch(err => status.innerText = "Error: " + err);
        }

        // Detect trigger phrase after dictation settles
        textbox.addEventListener('input', function() {
            status.innerText = "Listening...";
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                const text = textbox.value;
                if (TRIGGER.test(text)) {
                    const message = text.replace(TRIGGER, '').trim();
                    sendToCAS(message);
                }
            }, 1500);
        });

        // Manual send button
        sendBtn.addEventListener('click', function() {
            sendToCAS(textbox.value);
        });

        // Clear button
        clearBtn.addEventListener('click', function() {
            textbox.value = "";
            status.innerText = "Cleared";
            textbox.focus();
        });
    </script>
</body>
</html>
"""


@app.route('/')
def home():
    return render_template_string(HTML_PAGE)


@app.route('/send-to-cas', methods=['POST'])
def send_to_cas_route():
    text = request.data.decode('utf-8').strip()
    if not text:
        return "Empty message", 400

    if REMOTE_AUDIO:
        # Synchronous mode: wait for CAS response, then serve audio
        since_time = time.time() - 1  # 1-second buffer for clock skew
        print(f"\n[Sent to CAS (remote audio)]: {text[:80]}...")

        try:
            send_to_cas_sync(text)
        except Exception as e:
            print(f"[CAS Error]: {e}")
            return "CAS request failed", 502

        # Wait for TTS audio file to appear
        print("[Audio] Waiting for TTS audio file...")
        audio_path = wait_for_new_audio(since_time, timeout=90)
        if audio_path:
            print(f"[Audio] Serving: {os.path.basename(audio_path)}")
            return send_file(audio_path, mimetype='audio/wav')
        else:
            print("[Audio] Timed out waiting for audio file")
            return "Audio generation timed out", 504
    else:
        # Fire-and-forget mode (default)
        send_to_cas_async(text)
        print(f"\n[Sent to CAS]: {text[:80]}...")
        return "OK", 200


@app.route('/send-to-clipboard', methods=['POST'])
def send_to_clipboard_route():
    text = request.data.decode('utf-8').strip()
    if not text:
        return "Empty message", 400
    pyperclip.copy(text)
    print(f"\n[Clipboard]: {text[:80]}...")
    return "OK", 200


if __name__ == '__main__':
    print("Server running. Open this IP on your phone:")
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
    print(f"http://{local_ip}:5000")
    print(f"Trigger phrase: say \"{TRIGGER_PHRASE}\" to send to CAS")

    app.run(host='0.0.0.0', port=5000)
