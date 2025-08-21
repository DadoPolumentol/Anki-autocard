# media_utils.py
import os
import re
from tkinter import Tk
from tkinter.filedialog import askdirectory

# Recognized image extensions (order doesn't matter)
IMAGE_EXTS = ("png", "jpg", "jpeg", "gif", "webp", "bmp")

# Regex to find image placeholders like:
# Slika 1, slika1, sl 1, sl1, slika_01, SL 001 etc.
# captures the number in group 1
_PLACEHOLDER_RE = re.compile(r'\b(?:slika|sl)?_?\s*0*(\d+)\b', flags=re.I)


def _find_image_for_number(image_folder, number, files_list):
    """
    Try to find a filename in image_folder that matches the placeholder number.
    Matching rules (case-insensitive):
      - 1.png
      - sl1.jpg
      - slika1.jpeg
      - sl_1.png
      - slika_01.jpg
    Returns the actual filename (basename) if found, else None.
    """
    # Build pattern allowing optional prefix and optional underscore and leading zeros
    exts_pattern = "|".join(IMAGE_EXTS)
    pattern = re.compile(rf'^(?:slika|sl)?_?0*{re.escape(number)}\.(?:{exts_pattern})$', flags=re.I)

    for fname in files_list:
        if pattern.match(fname):
            return fname
    return None


def process_blocks(blocks, initial_dir=None):
    """
    Process a list of text blocks (strings). Replace placeholders with <img src="..."> tags if images are found.
    If no placeholders are present, returns (blocks, []) immediately.
    If placeholders exist, prompts the user for an image folder (askdirectory).
      - If user chooses a folder, it will try to find matching images and replace placeholders.
      - If user cancels, no replacements are made (original text returned) and media_files list is empty.
    Returns: (processed_blocks, media_files_list)
      - processed_blocks: list of strings (same length as input blocks)
      - media_files_list: list of full paths to media files to pass into genanki (unique)
    """
    # Quick scan for placeholders
    placeholders_found = False
    for b in blocks:
        if _PLACEHOLDER_RE.search(b):
            placeholders_found = True
            break

    if not placeholders_found:
        return blocks, []

    # Ask user to choose an image folder
    print("Image placeholders found in text.")
    print("Please choose your image folder (Cancel to skip images).")
    Tk().withdraw()
    image_folder = askdirectory(initialdir=initial_dir or os.getcwd(), title="Select folder with images (Cancel to skip)")
    if not image_folder:
        print("No image folder selected — proceeding without inserting images.")
        return blocks, []

    # Prepare file list (case preserved)
    try:
        files_list = os.listdir(image_folder)
    except Exception as e:
        print("Could not list files in the selected folder:", e)
        return blocks, []

    media_set = set()
    processed = []

    for block_idx, block in enumerate(blocks):
        # Replacement function for re.sub
        def _replace(match):
            number = match.group(1)
            found = _find_image_for_number(image_folder, number, files_list)
            if found:
                media_set.add(os.path.join(image_folder, found))
                # Use basename in src so genanki uses packaged filename
                return f'<div><img src="{os.path.basename(found)}" alt="Image {number}"></div>'
            else:
                # If no matching image, keep the original placeholder text unchanged
                print(f"Warning: no image found for placeholder '{match.group(0)}' (block {block_idx+1}).")
                return match.group(0)

        new_block = _PLACEHOLDER_RE.sub(_replace, block)
        processed.append(new_block)

    media_files = list(media_set)
    if media_files:
        print(f"Found {len(media_files)} image(s) to include.")
    else:
        print("No matching image files were found in the selected folder.")

    return processed, media_files
