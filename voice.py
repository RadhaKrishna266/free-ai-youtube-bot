# voice.py
import subprocess
import tempfile
import os

def create_voice(text, name):
    output_file = f"{name}.mp3"

    # Clean text aggressively for TTS safety
    safe_text = (
        text.replace('"', "'")
        .replace("\n", " ")
        .replace("-", " ")
    )

    # Write text to temp file (IMPORTANT)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w") as f:
        f.write(safe_text)
        text_file = f.name

    cmd = [
        "edge-tts",
        "--voice", "en-US-GuyNeural",
        "--text-file", text_file,
        "--write-media", output_file
    ]

    try:
        subprocess.run(cmd, timeout=180, check=True)
    except subprocess.CalledProcessError as e:
        raise Exception(f"Edge TTS failed: {e}")
    finally:
        os.remove(text_file)

    return output_file