import subprocess
import re

def sanitize_text(text):
    text = text.replace("\n", " ")
    text = text.replace("—", "-")
    text = text.replace("–", "-")
    text = text.replace(":", "")
    text = text.replace('"', "'")
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def create_voice(text, name):
    output_file = f"{name}.mp3"

    safe_text = sanitize_text(text)
    safe_text = safe_text[:2000]  # CI-safe limit

    command = [
        "edge-tts",
        "--voice", "en-US-GuyNeural",
        "--rate", "+0%",
        "--pitch", "+0Hz",
        "--text", safe_text,
        "--write-media", output_file,
    ]

    try:
        subprocess.run(command, timeout=180, check=True)
    except subprocess.TimeoutExpired:
        raise Exception("Voice generation timed out")
    except subprocess.CalledProcessError as e:
        raise Exception(f"Edge TTS failed: {e}")

    return output_file