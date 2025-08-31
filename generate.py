import genanki
import os
import random
import subprocess
import re
from tkinter import Tk
from tkinter.filedialog import askopenfilename
from media_utils import process_blocks

PROMPTS_FOLDER = "prompts"
TEMP_FOLDER = "temp"
PROMPT_FILES = ["minimal.txt", "medium.txt", "maximum.txt"]



# --- helper: normalize text (strip "Question:" / "Answer:") ---
def clean_text(s: str) -> str:
    s = s.strip()
    if s.lower().startswith("question:"):
        s = s[len("question:"):].strip()
    if s.lower().startswith("answer:"):
        s = s[len("answer:"):].strip()
    return s

# --- step 1: generate prompts ---
def generate_prompts(user_text: str):
    os.makedirs(TEMP_FOLDER, exist_ok=True)
    prompts = []
    for filename in PROMPT_FILES:
        prompt_path = os.path.join(PROMPTS_FOLDER, filename)
        if not os.path.exists(prompt_path):
            print(f"Prompt file not found: {prompt_path}")
            continue

        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_text = f.read()

        filled = prompt_text.replace("[INSERT YOUR TEXT HERE]", user_text)

        # Save to temp
        output_path = os.path.join(TEMP_FOLDER, filename)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(filled)
        print(f"Created: {output_path}")

        prompts.append(filled)
    return prompts

# --- step 2: collect Q/A pairs ---
def extract_qa_pairs(text):
    """Extract Q/A pairs from any input format, clean Question/Answer labels, strip **."""
    pattern = re.compile(r"Question[:\s]*(.*?)Answer[:\s]*(.*?)(?=Question|$)", re.IGNORECASE | re.DOTALL)
    matches = pattern.findall(text)

    qa_pairs = []
    for q, a in matches:
        q = q.strip()
        a = a.strip().replace("**", "")
        if q and a:
            qa_pairs.append((q, a))

    # fallback if regex fails: split by blank lines
    if not qa_pairs:
        blocks = [b.strip() for b in text.split("\n\n") if b.strip()]
        for i in range(0, len(blocks), 2):
            if i + 1 < len(blocks):
                qa_pairs.append((blocks[i], blocks[i + 1]))

    return qa_pairs

# --- updated collect functions ---
def collect_qa_from_file(path):
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    qa_pairs = extract_qa_pairs(text)
    # process all questions and answers for images
    processed_blocks, media_files = process_blocks([q for pair in qa_pairs for q in pair], initial_dir=os.path.dirname(path))
    # re-pair after image processing
    qa_pairs = [(processed_blocks[i], processed_blocks[i+1]) for i in range(0, len(processed_blocks), 2)]
    return qa_pairs, media_files

def collect_qa_from_input():
    print("Paste your Q/A text here (blank line to finish):")
    lines = []
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)
    text = "\n".join(lines)
    qa_pairs = extract_qa_pairs(text)
    processed_blocks, media_files = process_blocks([q for pair in qa_pairs for q in pair])
    qa_pairs = [(processed_blocks[i], processed_blocks[i+1]) for i in range(0, len(processed_blocks), 2)]
    return qa_pairs, media_files


# --- step 3: build deck ---
def build_deck(name, qa_pairs, media_files):
    DECK_ID = random.randrange(1 << 30, 1 << 31)
    MODEL_ID = random.randrange(1 << 30, 1 << 31)

    deck = genanki.Deck(DECK_ID, name)
    model = genanki.Model(
        MODEL_ID,
        "Q/A Model",
        fields=[{"name": "Question"}, {"name": "Answer"}],
        templates=[{
            "name": "Card",
            "qfmt": "{{Question}}",
            "afmt": "{{FrontSide}}<hr id='answer'>{{Answer}}",
        }],
    )

    for q, a in qa_pairs:
        note = genanki.Note(model=model, fields=[q, a])
        deck.add_note(note)

    output_file = f"{name}.apkg"
    if media_files:
        genanki.Package(deck, media_files=media_files).write_to_file(output_file)
    else:
        genanki.Package(deck).write_to_file(output_file)

    print(f"Deck saved as {output_file}")
    try:
        subprocess.Popen([output_file], shell=True)
        print("Deck opened in Anki.")
    except Exception as e:
        print("Could not open deck automatically:", e)

# --- main flow ---
def main():
    # 1. Input text for prompt generation
    print("Paste your text (finish with blank line):")
    lines = []
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)
    user_text = "\n".join(lines)

    prompts = generate_prompts(user_text)

    # 2. Show prompts one by one
    print("\n--- Generated Prompts ---")
    for i, p in enumerate(prompts, start=1):
        print(f"\nPrompt {i}:\n{'='*40}\n{p}\n{'='*40}")
        input("Press Enter to continue...")

    # 3. Ask how many decks
    while True:
        try:
            n = int(input("\nHow many decks do you want to create? (1-3): "))
            if n in (1, 2, 3):
                break
        except ValueError:
            pass
        print("Please enter 1, 2, or 3.")

    # 4. For each deck, ask for source (file or paste)
    for d in range(1, n + 1):
        print(f"\nDeck {d}:")
        choice = input("Use file (f) or paste text (p)? ").strip().lower()
        if choice.startswith("f"):
            Tk().withdraw()
            path = askopenfilename(title=f"Select Q/A text file for Deck {d}",
                                   filetypes=[("Text files", "*.txt")])
            if not path:
                print("No file selected, skipping this deck.")
                continue
            qa_pairs, media_files = collect_qa_from_file(path)
            name = os.path.splitext(os.path.basename(path))[0]
        else:
            qa_pairs, media_files = collect_qa_from_input()
            name = f"deck_{d}"

        if qa_pairs:
            build_deck(name, qa_pairs, media_files)
        else:
            print(f"No Q/A pairs found for Deck {d}, skipping.")

if __name__ == "__main__":
    main()
