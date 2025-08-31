import os
import sys
import pyperclip

# Ask user for text input
def get_input_text():
    if not sys.stdin.isatty():  # piped from file/redirect
        return sys.stdin.read().strip()
    elif len(sys.argv) > 1:  # passed as command-line argument
        return " ".join(sys.argv[1:])
    else:  # fallback to clipboard
        print("⚡ No input provided, using clipboard text...")
        return pyperclip.paste().strip()

user_text = get_input_text()
print("=== INPUT TEXT START ===")
print(user_text)
print("=== INPUT TEXT END ===")

# Folders
prompts_folder = "prompts"
output_folder = "temp"

# Create output folder if it doesn't exist
os.makedirs(output_folder, exist_ok=True)

# Prompt files
prompt_files = ["minimal.txt", "medium.txt", "maximum.txt"]

for filename in prompt_files:
    prompt_path = os.path.join(prompts_folder, filename)
    if not os.path.exists(prompt_path):
        print(f"Prompt file not found: {prompt_path}")
        continue

    # Read the prompt template
    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt_text = f.read()

    # Replace placeholder with user text
    prompt_text = prompt_text.replace("[INSERT YOUR TEXT HERE]", user_text)

    # Save to temp folder
    output_path = os.path.join(output_folder, filename)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(prompt_text)

    print(f"Created: {output_path}")

print("All prompts generated in 'temp' folder.")
