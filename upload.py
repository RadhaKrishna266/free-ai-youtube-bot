import os
import json
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

IMAGE_COUNT = 90
RESOLUTION = "1280x720"

IMAGE_DIR = "images"
SCRIPT_FILE = "script.txt"
AUDIO_FILE = "voice.mp3"
VIDEO_FILE = "output.mp4"

# =========================================


def run(cmd):
    subprocess.run(cmd, check=True)


# ---------- SCRIPT ----------

def generate_script():
    base = (
        f"Today we explore {TOPIC}. "
        "One of the most mysterious ancient structures on Earth. "
        "Built thousands of years ago, its purpose remains debated by scientists. "
        "Many believe it was used for astronomy, rituals, or ancient ceremonies. "
    )

    words = (base * 80).split()
    script = " ".join(words[:TARGET_MINUTES * WORDS_PER_MIN])

    Path(SCRIPT_FILE).write_text(script)
    return script


# ---------- VOICE ----------

def generate_voice():
    print("🔊 Generating voice narration...")

    run([
        "edge-tts",
        "--voice", VOICE,
        "--rate=-15%",
        "--file", SCRIPT_FILE,
        "--write-media", AUDIO_FILE
    ])


# ---------- IMAGES ----------

def download_images():
    print("🖼️ Downloading images...")
    Path(IMAGE_DIR).mkdir(exist_ok=True)

    for i in range(IMAGE_COUNT):
        out = f"{IMAGE_DIR}/img_{i:03d}.jpg"
        url = f"https://picsum.photos/1280/720?random={i}"
        run(["curl", "-L", url, "-o", out])


# ---------- VIDEO ----------

def create_video():
    print("🎞️ Creating animated video...")

    run([
        "ffmpeg", "-y",
        "-framerate", "1/7",
        "-i", f"{IMAGE_DIR}/img_%03d.jpg",
        "-i", AUDIO_FILE,
        "-vf",
        "zoompan=z='min(zoom+0.0015,1.2)':d=175:s=1280x720",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-shortest",
        VIDEO_FILE
    ])


# ---------- YOUTUBE ----------

def load_credentials():
    raw = os.getenv("YOUTUBE_CLIENT_SECRET")
    if not raw:
        print("⚠️ No YouTube credentials found — skipping upload")
        return None

    return Credentials.from_authorized_user_info(
        json.loads(raw),
        ["https://www.googleapis.com/auth/youtube.upload"]
    )


def upload_to_youtube():
    creds = load_credentials()
    if not creds:
        return

    print("🚀 Uploading to YouTube...")

    youtube = build("youtube", "v3", credentials=creds)

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": TOPIC,
                "description": f"Full documentary about {TOPIC}",
                "categoryId": "27",
            },
            "status": {"privacyStatus": "public"}
        },
        media_body=MediaFileUpload(VIDEO_FILE, resumable=True)
    )

    response = request.execute()
    print("✅ Uploaded video ID:", response["id"])


# ---------- MAIN ----------

def main():
    print("🚀 Starting full animated video pipeline")

    generate_script()
    generate_voice()
    download_images()
    create_video()
    upload_to_youtube()


if __name__ == "__main__":
    main()