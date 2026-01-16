# voice.py
import subprocess
import tempfile
import os

def create_voice(text, name):
    output_file = f"{name}.mp3"

    # Write text to temp file (safe for long scripts)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w") as f:
        f.write(text)
        text_file = f.name

    cmd = [
        "edge-tts",
        "--voice", "en-US-GuyNeural",
        "--file", text_file,
        "--write-media", output_file
    ]

    try:
        subprocess.run(cmd, timeout=180, check=True)
    finally:
        os.remove(text_file)

    return output_file