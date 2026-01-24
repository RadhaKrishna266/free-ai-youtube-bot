import os
import json
import base64
import subprocess
import requests
from TTS.api import TTS
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ================= CONFIG =================
os.environ["COQUI_TOS_AGREED"] = "1"

PIXABAY_KEY = os.environ["PIXABAY_API_KEY"]

SCRIPT_FILE = "script.txt"
VOICE_FILE = "narration.wav"

SPEAKER_WAV = "audio/speaker.wav"
TANPURA_FILE = "audio/tanpura.mp3"
BELL_FILE = "audio/temple_bell.mp3"

FINAL_VIDEO = "final.mp4"

TTS_MODEL_NAME = "tts_models/multilingual/multi-dataset/xtts_v2"
# =========================================


def run(cmd):
    subprocess.run(cmd, check=True)


# ================= AUDIO =================
def create_audio():
    print("🎤 Creating NATURAL Hindi voice")

    if not os.path.exists(SPEAKER_WAV):
        raise RuntimeError("❌ audio/speaker.wav is REQUIRED")

    with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
        text = f.read().strip()

    tts = TTS(TTS_MODEL_NAME, gpu=False)

    tts.tts_to_file(
        text=text,
        file_path=VOICE_FILE,
        speaker_wav=SPEAKER_WAV,
        language="hi"
    )

    print("✅ Hindi narration created")


# ================= VIDEO =================
def create_video():
    run([
        "ffmpeg", "-y",
        "-loop", "1", "-i", "images/000.jpg",
        "-i", VOICE_FILE,
        "-stream_loop", "-1", "-i", TANPURA_FILE,
        "-stream_loop", "-1", "-i", BELL_FILE,
        "-filter_complex",
        "[2:a]volume=0.25[a2];"
        "[3:a]volume=0.12[a3];"
        "[1:a][a2][a3]amix=inputs=3[a]",
        "-map", "0:v",
        "-map", "[a]",
        "-t", "600",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        FINAL_VIDEO
    ])


# ================= MAIN =================
def main():
    create_audio()
    create_video()


if __name__ == "__main__":
    main()