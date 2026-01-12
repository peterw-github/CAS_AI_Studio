import logging
from flask import Flask, request, render_template_string
import pyperclip

# Disable standard Flask logging to keep the console clean
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)

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
            box-sizing: border-box; /* Ensures padding doesn't break width */
        }
        .status { margin-top: 10px; color: #00ff00; font-size: 14px; margin-bottom: 10px; }

        /* New Button Styles */
        button {
            width: 100%; 
            padding: 15px; 
            font-size: 18px; 
            background-color: #CF6679; /* A nice muted red */
            color: #000; 
            border: none; 
            border-radius: 8px;
            font-weight: bold;
            cursor: pointer;
        }
        button:active { background-color: #b00020; } /* Darker red when pressed */
    </style>
</head>
<body>
    <h3>🔴 Live Voice-to-Clipboard</h3>
    <textarea id="textbox" placeholder="Tap microphone on Gboard and speak..."></textarea>
    <div id="status" class="status">Ready</div>

    <button id="clearBtn">Clear Text</button>

    <script>
        const textbox = document.getElementById('textbox');
        const status = document.getElementById('status');
        const clearBtn = document.getElementById('clearBtn');
        let timeout = null;

        // NEW: Clear button logic
        clearBtn.addEventListener('click', function() {
            textbox.value = "";
            status.innerText = "Cleared";
            textbox.focus(); // Keeps the keyboard open so you can keep talking
        });

        // Send text to Python whenever input changes
        textbox.addEventListener('input', function() {
            status.innerText = "Sending...";

            // Debounce: Wait 2000ms after user stops talking/typing to send
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                fetch('/sync', {
                    method: 'POST',
                    headers: {'Content-Type': 'text/plain'},
                    body: textbox.value
                })
                .then(response => {
                    if (response.ok) status.innerText = "Synced to PC Clipboard";
                })
                .catch(err => status.innerText = "Error: " + err);
            }, 2000);
        });
    </script>
</body>
</html>
"""


@app.route('/')
def home():
    return render_template_string(HTML_PAGE)


@app.route('/sync', methods=['POST'])
def sync_clipboard():
    text = request.data.decode('utf-8')
    pyperclip.copy(text)
    print(f"\r[Received]: {text[:50]}...", end="", flush=True)
    return "OK", 200


if __name__ == '__main__':
    # host='0.0.0.0' allows other devices on the network (your phone) to connect
    print("Server running. Open this IP on your phone:")
    # This automatically finds your local IP address
    import socket

    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    print(f"http://{local_ip}:5000")

    app.run(host='0.0.0.0', port=5000)