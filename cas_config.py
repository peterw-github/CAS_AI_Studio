# --- CAS Configuration ---

# --- PORTS & FILES ---
CHROME_DEBUG_PORT = "127.0.0.1:9222"
LATEST_MSG_FILE = "latest_message.md"
COMMAND_FILE = "command_queue.txt"
CWD_FILE = "cwd_state.txt"

# --- TIMING ---
DEFAULT_INTERVAL = 10 * 60  # 10 minutes in seconds
BRIDGE_LOOP_DELAY = 1       # Seconds between bridge loop iterations
CLIPBOARD_TIMEOUT = 5

# --- VOICE SETTINGS ---
VIBEVOICE_URL = "https://9f48cfb90a4585d0d5.gradio.live"  # Update if expired
VOICE_SPEAKER = "Just Keep Your Head Down, - Halo 3"
VOICE_CFG_SCALE = 1.1
DISABLE_CLONE = False

# Paragraph spacing for TTS:
# 0 = All paragraphs merged (no tone variation)
# 1 = Single newline between paragraphs (distinct tone per paragraph)
# 2+ = Multiple newlines (more pausing/variation)
VOICE_PARAGRAPH_SPACING = 1

# Smart merge: Adjacent lines get merged for TTS (overrides PARAGRAPH_SPACING)
VOICE_SMART_MERGE = True

# --- OUTPUT DIRS ---
OUTPUT_AUDIO_DIR = "AudioFiles"
OUTPUT_TEXT_DIR = "TextFiles"

# --- SCREEN VISION ---
MONITORS = 0  # 0 = all monitors, 1/2/3 = specific monitor

# --- SCREEN RECORDING ---
SCREEN_RECORDING_DURATION = 10  # Seconds (AI cannot change this)

# --- FILE ATTACHMENT PROCESSING ---
FILE_ATTACHMENT_WAIT = 5  # Seconds to wait for AI Studio to process attachments

# --- NAVIGATION ---
# "Home Base" directory for file operations
AI_START_DIR = r"D:\GoogleDrive\Core\Cortana"
