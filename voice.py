# voice.py
import subprocess
import tempfile
import os

def create_voice(text, name):
    output_file = f"{name}.mp3"

    # Edge TTS becomes unstable with very long input
    text = text.strip()[:1000]

    # Write text to a temporary file (MOST STABLE METHOD)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8") as f:
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
        # Clean up temp file
        if os.path.exists(text_file):
            os.remove(text_file)

    return output_file