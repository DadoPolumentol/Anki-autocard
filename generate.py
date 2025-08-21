import genanki
from tkinter import Tk
from tkinter.filedialog import askopenfilename
import os
import random
import subprocess

from media_utils import process_blocks  # new helper

# File to remember last folder
LAST_FOLDER_FILE = "last_folder.txt"

# Determine initial folder for dialog
if os.path.exists(LAST_FOLDER_FILE):
    with open(LAST_FOLDER_FILE, "r", encoding="utf-8") as f:
        initial_dir = f.read().strip()
        if not os.path.isdir(initial_dir):
            initial_dir = os.getcwd()
else:
    initial_dir = os.getcwd()

# Hide the main Tk window
Tk().withdraw()

# Open file dialog
file_path = askopenfilename(
    title="Select your Q/A text file",
    initialdir=initial_dir,
    filetypes=[("Text files", "*.txt")]
)

if not file_path:
    print("No file selected. Exiting.")
    exit()

# Remember folder for next time
with open(LAST_FOLDER_FILE, "w", encoding="utf-8") as f:
    f.write(os.path.dirname(file_path))

# Get file name without extension
name = os.path.splitext(os.path.basename(file_path))[0]

INPUT_FILE = file_path
OUTPUT_FILE = f"{name}.apkg"

# Generate random IDs for deck and model
DECK_ID = random.randrange(1 << 30, 1 << 31)
MODEL_ID = random.randrange(1 << 30, 1 << 31)

# Load file
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    text = f.read()

# Split by blank lines
blocks = [b.strip() for b in text.split("\n\n") if b.strip()]

# --- NEW: process blocks for image placeholders ---
processed_blocks, media_files = process_blocks(blocks, initial_dir=os.path.dirname(file_path))

# Pair questions and answers from processed_blocks
qa_pairs = []
for i in range(0, len(processed_blocks), 2):
    if i + 1 < len(processed_blocks):
        question = processed_blocks[i]
        answer = processed_blocks[i + 1]
        qa_pairs.append((question, answer))

# Define deck and model
deck = genanki.Deck(DECK_ID, name)
model = genanki.Model(
    MODEL_ID,
    "Q/A Model",
    fields=[
        {"name": "Question"},
        {"name": "Answer"},
    ],
    templates=[
        {
            "name": "Card",
            "qfmt": "{{Question}}",
            "afmt": "{{FrontSide}}<hr id='answer'>{{Answer}}",
        },
    ],
)

# Add notes
for q, a in qa_pairs:
    note = genanki.Note(
        model=model,
        fields=[q, a]
    )
    deck.add_note(note)

# Export deck (include media_files if any)
if media_files:
    genanki.Package(deck, media_files=media_files).write_to_file(OUTPUT_FILE)
else:
    genanki.Package(deck).write_to_file(OUTPUT_FILE)

print(f"Deck saved as {OUTPUT_FILE}")

# Automatically open in Anki
try:
    subprocess.Popen([OUTPUT_FILE], shell=True)
    print("Deck opened in Anki.")
except Exception as e:
    print("Could not open deck automatically:", e)
