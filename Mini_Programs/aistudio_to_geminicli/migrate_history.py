import json
import uuid
import datetime

# --- CONFIG ---
INPUT_FILE = "ai_studio_format.json"
OUTPUT_FILE = "session-2026-01-28T07-04-b34e4059.json"  # <--- UPDATED
HARDCODED_SESSION_ID = "b34e4059-4863-4e8c-aeb7-785f2cd304bd" # <--- UPDATED
START_TIME = datetime.datetime(2000, 1, 1, 12, 0, 0)


def convert_ai_studio_to_cli():
    print(f"Reading {INPUT_FILE}...")

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        ai_data = json.load(f)

    cli_messages = []
    current_time = START_TIME

    # Iterate through AI Studio's "chunks"
    # Note: AI Studio puts all chunks in "chunkedPrompt", not strictly sequential messages array.
    # We need to flatten the "chunks" list.

    chunks = ai_data.get("chunkedPrompt", {}).get("chunks", [])

    for chunk in chunks:
        # Filtering out internal thoughts, as they aren't supposed to be in context window.
        if chunk.get("isThought"):
            continue

        # Determine Role
        role = chunk.get("role")
        if role == "model":
            cli_role = "gemini"
        else:
            cli_role = "user"

        # Get Text
        # AI Studio puts text in "text" field, OR split across "parts" if complex.
        # Prioritize the flattened "text" field if present.
        content = chunk.get("text", "")

        # If text is empty (sometimes happens with thought-only chunks?), look at parts
        if not content and "parts" in chunk:
            parts = chunk["parts"]
            content = "".join([p.get("text", "") for p in parts])

        if not content.strip():
            continue  # Skip empty messages

        # Build CLI Message Object
        msg_id = str(uuid.uuid4())
        timestamp_str = current_time.isoformat() + "Z"

        message = {
            "id": msg_id,
            "timestamp": timestamp_str,
            "type": cli_role,
            "content": content
        }

        # If it's a model response, the CLI usually expects a 'thoughts' array and 'tokens' object.
        # We can fake these to avoid schema validation errors.
        if cli_role == "gemini":
            message["thoughts"] = []
            message["tokens"] = {
                "input": 0,
                "output": len(content) // 4,  # Crude estimate
                "total": 0
            }
            message["model"] = "gemini-3-pro-preview"  # Force the model name

        cli_messages.append(message)

        # Increment fake time by 1 minute
        current_time += datetime.timedelta(minutes=1)

    # Build Final CLI Session JSON
    cli_session = {
        "sessionId": HARDCODED_SESSION_ID,
        "projectHash": "dc92e103f202a66699efa2fc772d44d0716c4c456dc11df33ce591ed884d2608",
        "startTime": START_TIME.isoformat() + "Z",
        "lastUpdated": current_time.isoformat() + "Z",
        "messages": cli_messages
    }

    print(f"Writing {len(cli_messages)} messages to {OUTPUT_FILE}...")

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(cli_session, f, indent=2)

    print("Migration Complete.")


if __name__ == "__main__":
    convert_ai_studio_to_cli()