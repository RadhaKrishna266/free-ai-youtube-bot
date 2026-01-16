# voice.py
import subprocess

def create_voice(text, name):
    output_file = f"{name}.mp3"

    # Clean text for CLI safety
    safe_text = text.replace('"', "'").replace("\n", " ")

    cmd = [
        "edge-tts",
        "--voice", "en-US-GuyNeural",
        "--text", safe_text,
        "--write-media", output_file
    ]

    try:
        subprocess.run(cmd, timeout=180, check=True)
    except subprocess.TimeoutExpired:
        raise Exception("Voice generation timed out")
    except subprocess.CalledProcessError as e:
        raise Exception(f"Edge TTS failed: {e}")

    return output_file