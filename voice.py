# voice.py
import subprocess
import tempfile
import os

def create_voice(text, name):
    output_file = f"{name}.mp3"

    # Edge TTS is unstable with long text → limit length
    text = text.strip()[:1000]

    # Write text to temp file (MOST STABLE METHOD)
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