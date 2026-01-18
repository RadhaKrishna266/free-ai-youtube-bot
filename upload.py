import os
import random
import subprocess
from datetime import datetime

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

# -------------------------
# CONFIG
# -------------------------
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN_FILE = "token.json"
BACKGROUND_IMAGE = "assets/background.jpg"
OUTPUT_VIDEO = "output.mp4"
OUTPUT_AUDIO = "voice.mp3"

# -------------------------
# TOPIC PICKER
# -------------------------
def pick_topic():
    category = random.choice(["history", "tech"])
    with open(f"topics/{category}.txt", "r") as f:
        topic = random.choice(f.readlines()).strip()
    return category, topic

# -------------------------
# SCRIPT GENERATOR (FREE)
# -------------------------
def generate_script(category, topic):
    if category == "history":
        return (
            f"Did you know? {topic}. "
            f"This moment changed history forever. "
            f"Many people still don't know this fact. "
            f"History is full of surprises."
        )
    else:
        return (
            f"Let’s understand {topic}. "
            f"It works in a very simple way. "
            f"This technology affects our daily life more than you think. "
            f"Technology is shaping the future."
        )

# -------------------------
# VOICE GENERATION (EDGE TTS)
# -------------------------
def generate_voice(text):
    subprocess.run([
        "edge-tts",
        "--voice", "en-US-GuyNeural",
        "--text", text,
        "--write-media", OUTPUT_AUDIO
    ], check=True)

# -------------------------
# VIDEO CREATION (FFMPEG)
# -------------------------
def create_video():
    subprocess.run([
        "ffmpeg",
        "-y",
        "-loop", "1",
        "-i", BACKGROUND_IMAGE,
        "-i", OUTPUT_AUDIO,
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        OUTPUT_VIDEO
    ], check=True)

# -------------------------
# YOUTUBE UPLOAD
# -------------------------
def upload_video(title, description):
    creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    youtube = build("youtube", "v3", credentials=creds)

    body = {
        "snippet": {
            "title": title[:95],
            "description": description,
            "categoryId": "27",
        },
        "status": {
            "privacyStatus": "public"
        }
    }

    media = MediaFileUpload(OUTPUT_VIDEO, resumable=True)

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Upload progress: {int(status.progress() * 100)}%")

    print("UPLOAD SUCCESS:", response["id"])

# -------------------------
# MAIN
# -------------------------
def main():
    category, topic = pick_topic()
    print("Topic:", topic)

    script = generate_script(category, topic)
    generate_voice(script)
    create_video()

    today = datetime.utcnow().strftime("%Y-%m-%d")
    title = f"{topic} | {today}"
    description = script

    upload_video(title, description)

if __name__ == "__main__":
    main()