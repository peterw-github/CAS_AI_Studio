# --- START OF FILE cas_config.py ---

# --- PORTS & FILES ---
CHROME_DEBUG_PORT = "127.0.0.1:9222"
LATEST_MSG_FILE = "latest_message.md"
COMMAND_FILE = "command_queue.txt"
CWD_FILE = "cwd_state.txt"

# --- TIMING ---
DEFAULT_INTERVAL = 10 * 60
BRIDGE_LOOP_DELAY = 1
CLIPBOARD_TIMEOUT = 5

# --- VOICE SETTINGS ---
VIBEVOICE_URL = "https://bf55031b131ce24043.gradio.live/" # Update if expired
VOICE_SPEAKER = "Just Keep Your Head Down, - Halo 3" # List of voices available are in 'Emotional Tones' folder. 'Just keep your head down' with CFG 1.1 - 1.3 is good.
VOICE_CFG_SCALE = 1.1
DISABLE_CLONE = False

# Below is a tweak on how many 'new lines' between each paragraph, for the text that will be sent to the TTS.
VOICE_PARAGRAPH_SPACING = 1
# 0 = All paragraphs on one line (merged). So tone doesn't vary between paragraphs, since there are no paragraphs for the TTS.
# 1 = Each paragraph starts on a new line, no empty lines between. Tone will now DISTINCTLY vary between paragraphs most likely.
# 2 = Now there's a single empty line between paragraph.
# 4 = Now there's three empty lines between paragraph. Tone should vary THE MOST between paragraphs, although there might be excessive pausing

# Below is a toggle on whether two lines of text in AI Studio that are on adjacent lines, get merged onto a single line for the TTS.
# Warning. Overrides `VOICE_PARAGRAPH_SPACING` if set to True.
VOICE_SMART_MERGE = True

# --- OUTPUT DIRS ---
OUTPUT_AUDIO_DIR = "AudioFiles"
OUTPUT_TEXT_DIR = "TextFiles"  # <--- NEW

# --- SCREEN SCREENSHOT VISION ---
MONITORS = 0 # 0 for all monitors. 1, 2, and 3, respectively represent the monitors 'identified' by Windows, in display settings.


# --- SCREEN RECORDING VISION ---
SCREEN_RECORDING_DURATION = 10  # Seconds. (AI cannot change this)

# --- NAVIGATION ---
# NEW: The "Home Base" for Cortana. Use raw string r"" for Windows paths.
AI_START_DIR = r"D:\GoogleDrive\Core\Cortana"