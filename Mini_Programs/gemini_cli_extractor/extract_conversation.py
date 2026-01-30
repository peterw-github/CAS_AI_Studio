#!/usr/bin/env python3
"""
Extracts conversation text from JSON payload files and outputs to markdown.

Automatically scans the current folder for any .json files, then reads the
'request.contents' section and pulls out the first 'text' element from each
message's 'parts' array, ignoring tools and other data types.
"""

import json
from pathlib import Path


def extract_conversations(json_path: Path) -> list[dict]:
    """
    Extract conversation messages from a JSON file.
    
    Args:
        json_path: Path to the JSON file
        
    Returns:
        List of dicts with 'role' and 'text' keys
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    messages = []
    
    # Navigate to request.contents
    contents = data.get('request', {}).get('contents', [])
    
    for item in contents:
        role = item.get('role', 'unknown')
        parts = item.get('parts', [])
        
        # Find the first 'text' element in parts
        first_text = None
        for part in parts:
            if 'text' in part:
                first_text = part['text']
                break
        
        if first_text is not None:
            messages.append({
                'role': role,
                'text': first_text
            })
    
    return messages


def format_as_markdown(messages: list[dict], filename: str) -> str:
    """
    Format extracted messages as markdown.
    
    Args:
        messages: List of message dicts with 'role' and 'text'
        filename: Name of the output file for the XML tag
        
    Returns:
        Formatted markdown string
    """
    lines = []
    
    # Opening XML tag with backticks
    lines.append(f'`<file name="{filename}">`')
    lines.append("")
    
    for i, msg in enumerate(messages, 1):
        role = msg['role']
        text = msg['text']
        
        # Format role as a header
        role_display = "**John:**" if role == "user" else "**Cortana:**"
        lines.append(f"### {role_display}")
        lines.append("")
        lines.append(text)
        lines.append("")
    
    # Closing XML tag with backticks
    lines.append("`</file>`")
    
    return "\n".join(lines)


def process_file(json_path: Path) -> bool:
    """
    Process a single JSON file and create corresponding markdown.
    
    Args:
        json_path: Path to the JSON file
        
    Returns:
        True if successful, False if skipped/failed
    """
    output_path = json_path.with_suffix('.md')
    
    try:
        messages = extract_conversations(json_path)
        
        # Skip files that don't have the expected structure
        if not messages:
            print(f"  Skipped (no messages found): {json_path.name}")
            return False
        
        markdown_content = format_as_markdown(messages, output_path.name)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"  ✓ {json_path.name} → {output_path.name} ({len(messages)} messages)")
        return True
        
    except (json.JSONDecodeError, KeyError) as e:
        print(f"  Skipped (invalid format): {json_path.name}")
        return False
    except Exception as e:
        print(f"  Error processing {json_path.name}: {e}")
        return False


def main():
    # Get the directory where the script is located
    script_dir = Path(__file__).parent.resolve()
    
    # Find all JSON files in the script's directory
    json_files = list(script_dir.glob('*.json'))
    
    if not json_files:
        print(f"No JSON files found in: {script_dir}")
        return
    
    print(f"Found {len(json_files)} JSON file(s) in: {script_dir}")
    print()
    
    successful = 0
    for json_file in sorted(json_files):
        if process_file(json_file):
            successful += 1
    
    print()
    print(f"Done! Processed {successful}/{len(json_files)} file(s)")


if __name__ == "__main__":
    main()
