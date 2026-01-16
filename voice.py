# voice.py
import subprocess
import tempfile
import os

def create_voice(text, name):
    output_file = f"{name}.mp3"

    # Write text to temp file (SAFE for CI)
    with tempfile.NamedTemporaryFile(delete=False, mode="w", suffix=".txt") as f:
        f.write(text)
        text_file = f.name

    cmd = [
        "edge-tts",
        "--voice", "en-US-GuyNeural",
        "--text-file", text_file,
        "--write-media", output_file
    ]

    try:
        subprocess.run(cmd, timeout=180, check=True)
    finally:
        os.remove(text_file)

    return output_file