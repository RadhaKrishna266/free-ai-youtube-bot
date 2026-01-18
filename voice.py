import subprocess
import tempfile
import re
import time

def clean_text(text):
    # remove symbols that break Edge TTS
    text = re.sub(r"[^a-zA-Z0-9.,!?\\s]", "", text)
    return text.strip()

def create_voice(text, name="audio"):
    text = clean_text(text)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
        f.write(text.encode("utf-8"))
        txt_path = f.name

    output = f"{name}.mp3"

    # VERY STABLE VOICE
    voice = "en-US-AriaNeural"

    # retry logic (important)
    for attempt in range(3):
        try:
            subprocess.run(
                [
                    "edge-tts",
                    "--voice", voice,
                    "--file", txt_path,
                    "--write-media", output
                ],
                check=True,
                timeout=180
            )
            return output
        except Exception as e:
            print(f"Voice attempt {attempt+1} failed, retrying...")
            time.sleep(5)

    raise RuntimeError("Voice generation failed after retries")