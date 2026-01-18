import os
import re

"""
WARNING: THIS PYTHON PROGRAM IS SPECIFICALLY DESIGNED TO ONLY WORK WITH 'AFTERGLOW MEMORIES', THAT ARE CREATED FROM 
'CHAPTERS'. IT SPECIFICALLY PULLS OUT THE 'TITLE', AND THAT'S IT. IT WILL NOT WORK ON ANY OTHER SORT OF MARKDOWN FILE,
UNLESS THAT MARKDOWN FILE HAS THE SAME 'IDENTITY FILE X: <TITLE> // ARCHIVED' PATTERN.
"""


def rename_afterglow_files():
    # 1. Get the folder where this script is currently running
    directory_path = os.path.dirname(os.path.abspath(__file__))

    print(f"Scanning directory: {directory_path}...\n")
    print("-" * 60)

    # ---------------------------------------------------------
    # PATTERN 1: Detect Volume and Number from the FILENAME
    # Matches: "Vol 49 - Afterglow 04" or similar variations
    # Group 1 = Volume Number (e.g. 49)
    # Group 2 = Afterglow Number (e.g. 04)
    # ---------------------------------------------------------
    filename_regex = re.compile(r"Vol\s+(\d+)\s*-\s*Afterglow\s*(\d+)", re.IGNORECASE)

    # ---------------------------------------------------------
    # PATTERN 2: Detect Title from the FILE CONTENT
    # Matches: [IDENTITY FILE 43: THE TITLE // ARCHIVED]
    # Group 1 = The Title
    # ---------------------------------------------------------
    content_regex = re.compile(r"\[IDENTITY FILE \d+:\s*(.*?)\s*\]")

    renamed_count = 0
    worked_on_files = []

    for filename in os.listdir(directory_path):
        # Filter: Must be .md
        if not filename.endswith(".md"):
            continue

        # EXCLUSION: Ignore any file named 'readme'
        if "readme" in filename.lower():
            continue

        # 2. Check if the filename is an "Afterglow" file
        name_match = filename_regex.search(filename)
        if not name_match:
            # If it's just a random markdown file (like 'Vol 49 - Ch 05.md'), skip it quietly.
            continue

        # Extract '49' and '04' from the filename
        vol_num = name_match.group(1)
        afterglow_num = name_match.group(2)

        file_path = os.path.join(directory_path, filename)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 3. Find the internal Identity Title
            title_match = content_regex.search(content)

            if title_match:
                # Extract Title
                raw_title = title_match.group(1).strip()

                # --- NEW LOGIC: FIX ALL CAPS ---
                # If the title is fully uppercase (e.g. "THE TITLE"), convert to Title Case ("The Title")
                if raw_title.isupper():
                    raw_title = raw_title.title()
                # -------------------------------

                # Sanitize Title (remove illegal chars like : / \ ?)
                safe_title = re.sub(r'[<>:"/\\|?*]', '', raw_title)

                # 4. Construct the Refac Filename
                # Format: Vol XX - Afterglow XX - <TITLE>.md
                new_filename = f"Vol {vol_num} - Afterglow {afterglow_num} - {safe_title}.md"
                new_file_path = os.path.join(directory_path, new_filename)

                # 5. Rename if different
                if filename != new_filename:
                    os.rename(file_path, new_file_path)
                    print(f"[RENAME] '{filename}'\n      -> '{new_filename}'")
                    worked_on_files.append(new_filename)
                    renamed_count += 1
                else:
                    print(f"[OK]     '{filename}' is already correct.")
                    worked_on_files.append(filename)
            else:
                print(f"[WARN]   '{filename}' matches naming pattern but has NO Identity Tag.")

        except Exception as e:
            print(f"[ERROR]  Could not process '{filename}': {e}")

    # Summary Output
    print("-" * 60)
    print(f"Processing Complete. Total files renamed: {renamed_count}")


if __name__ == "__main__":
    rename_afterglow_files()