# Conversation Extractor

A Python utility that extracts conversation text from JSON payload files and converts them into clean, readable Markdown files.

## Overview

This tool was designed to process JSON files containing conversation data between a user and a model (specifically structured for API payloads). It extracts the text content from each message and formats it as a Markdown document with clear speaker labels.

## Requirements

- Python 3.6 or higher
- No external dependencies (uses only standard library modules)

## Files

| File | Description |
|------|-------------|
| `extract_conversation.py` | The main Python script |
| `run_extractor.bat` | Windows batch file to run the script |
| `README.md` | This documentation file |

## Usage

### Option 1: Using the Batch File (Windows)

1. Place your `.json` files in the same folder as the script
2. Double-click `run_extractor.bat`
3. The script will process all JSON files and create corresponding `.md` files

### Option 2: Running Directly

1. Place your `.json` files in the same folder as the script
2. Open a terminal/command prompt in that folder
3. Run:
   ```
   python extract_conversation.py
   ```

## Expected JSON Structure

The script expects JSON files with the following structure:

```json
{
  "request": {
    "contents": [
      {
        "role": "user",
        "parts": [
          {
            "text": "Message content here..."
          }
        ]
      },
      {
        "role": "model",
        "parts": [
          {
            "text": "Response content here..."
          }
        ]
      }
    ]
  }
}
```

### Key Points

- The script navigates to `request.contents` to find messages
- Each message has a `role` (either `user` or `model`) and a `parts` array
- Only the **first** `text` element within `parts` is extracted
- Other data types (such as `inlineData` for images, or `tools`) are ignored

## Output Format

The script generates Markdown files with the following format:

```markdown
### John

User's message content here...

### Cortana

Model's response content here...

### John

Next user message...
```

- `user` messages are labeled as **John**
- `model` messages are labeled as **Cortana**
- Each speaker label is a level 3 heading (`###`)
- Messages are separated by blank lines for readability

## Behavior

- **Automatic scanning**: The script automatically finds all `.json` files in its directory
- **Smart skipping**: Files that don't match the expected structure are skipped gracefully
- **Same-name output**: Each `example.json` produces a corresponding `example.md`
- **Progress feedback**: The script reports which files were processed and how many messages were found

## Example Output

```
Found 3 JSON file(s) in: C:\Users\John\Conversations

  ✓ chat_01.json → chat_01.md (42 messages)
  ✓ chat_02.json → chat_02.md (18 messages)
  Skipped (no messages found): config.json

Done! Processed 2/3 file(s)
```

## Customisation

To modify speaker names or heading levels, edit the `format_as_markdown()` function in `extract_conversation.py`:

```python
role_display = "John" if role == "user" else "Cortana"
lines.append(f"### {role_display}")
```

## License

Free to use and modify.
