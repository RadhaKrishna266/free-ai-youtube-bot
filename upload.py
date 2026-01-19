import os
import json
import random
import subprocess
from pathlib import Path

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

# ================= CONFIG =================

TOPIC = "The Mystery of Stonehenge"
VOICE = "en-US-GuyNeural"

TARGET_MINUTES = 11
WORDS_PER_MIN = 140

IMAGE_COUNT = 80
FPS = 25
RESOLUTION = "1280x720"

AUDIO_FILE = "voice.mp3"
VIDEO_FILE = "output.mp4"

IMAGE_DIR = "images"

# =========================================


def run(cmd):
    subprocess.run(cmd, check=True)


# ---------- SCRIPT ----------

def generate_script():
    base = f"""
    Today we explore {TOPIC}. One of the greatest mysteries in human history.
    Built thousands of years ago, this ancient structure continues to puzzle scientists.
    Archaeologists debate its purpose, construction methods, and cultural significance.
    """
    words_needed = TARGET_MINUTES * WORDS_PER_MIN
    script = (" ".join([base] * 50)).split()[:words_needed]
    return " ".join(script)


# ---------- VOICE ----------

def generate_voice(script):
    print("🔊 Generating voice...")
    run([
        "edge-tts",
        "--voice", VOICE,
        "--rate", "+0%",
        "--text", script,
        "--write-media", AUDIO_FILE
    ])


# ---------- IMAGES ----------

def download_images():
    print("🖼️ Generating placeholder images...")
    Path(IMAGE_DIR).mkdir(exist_ok=True)
    for i in range(IMAGE_COUNT):
        run([
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"color=c=darkslategray:s={RESOLUTION}",
            "-frames:v", "1",
            f"{IMAGE_DIR}/img_{i:03d}.jpg"
        ])


# ---------- VIDEO ----------

def get_audio_duration():
    out = subprocess.check_output([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        AUDIO_FILE
    ])
    return float(out.strip())


def create_video():
    print("🎞️ Creating animated video...")
    duration = get_audio_duration()
    img_time = duration / IMAGE_COUNT

    run([
        "ffmpeg", "-y",
        "-framerate", f"1/{img_time}",
        "-i", f"{IMAGE_DIR}/img_%03d.jpg",
        "-i", AUDIO_FILE,
        "-vf",
        "zoompan=z='min(zoom+0.0015,1.15)':d=125:s=1280x720",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-shortest",
        VIDEO_FILE
    ])


# ---------- YOUTUBE ----------

def load_credentials():
    if os.path.exists("token.json"):
        return Credentials.from_authorized_user_file(
            "token.json",
            ["https://www.googleapis.com/auth/youtube.upload"]
        )

    raw = os.getenv("YOUTUBE_TOKEN_JSON")
    if not raw:
        raise RuntimeError("YOUTUBE_TOKEN_JSON missing")

    return Credentials.from_authorized_user_info(
        json.loads(raw),
        ["https://www.googleapis.com/auth/youtube.upload"]
    )


def upload_to_youtube():
    print("🚀 Uploading to YouTube...")
    creds = load_credentials()
    youtube = build("youtube", "v3", credentials=creds)

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": TOPIC,
                "description": f"Full documentary about {TOPIC}",
                "tags": ["history", "documentary", "ancient"],
                "categoryId": "27"
            },
            "status": {"privacyStatus": "public"}
        },
        media_body=MediaFileUpload(VIDEO_FILE, resumable=True)
    )

    response = request.execute()
    print("✅ Uploaded video ID:", response["id"])


# ---------- MAIN ----------

def main():
    print("🚀 Starting 10+ min animated video pipeline")

    script = generate_script()
    generate_voice(script)

    download_images()
    create_video()

    upload_to_youtube()


if __name__ == "__main__":
    main()