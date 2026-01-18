import os
import random
import subprocess
from datetime import datetime

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

# -------------------------
# CONSTANTS
# -------------------------
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

TOKEN_PATH = "token.json"
BACKGROUND_IMAGE = "assets/background.jpg"

AUDIO_FILE = "voice.mp3"
VIDEO_FILE = "output.mp4"

# -------------------------
# PICK RANDOM TOPIC
# -------------------------
def pick_topic():
    category = random.choice(["history", "tech"])
    file_path = f"topics/{category}.txt"

    with open(file_path, "r", encoding="utf-8") as f:
        topics = [line.strip() for line in f if line.strip()]

    return category, random.choice(topics)

# -------------------------
# SCRIPT GENERATION (FREE)
# -------------------------
def generate_script(category, topic):
    if category == "history":
        return (
            f"Did you know? {topic}. "
            "This event changed the world forever. "
            "Many people still don't know these facts. "
            "History is more interesting than fiction."
        )
    else:
        return (
            f"Let’s understand {topic}. "
            "It works in a very simple way. "
            "This technology impacts our daily life. "
            "Technology is shaping our future."
        )

# -------------------------
# TEXT TO SPEECH (EDGE TTS)
# -------------------------
def generate_voice(text):
    if os.path.exists(AUDIO_FILE):
        os.remove(AUDIO_FILE)

    subprocess.run(
        [
            "python",
            "-m",
            "edge_tts",
            "--voice",
            "en-US-GuyNeural",
            "--text",
            text,
            "--write-media",
            AUDIO_FILE,
        ],
        check=True,
    )

# -------------------------
# CREATE VIDEO USING FFMPEG
# -------------------------
def create_video():
    if os.path.exists(VIDEO_FILE):
        os.remove(VIDEO_FILE)

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-i",
            BACKGROUND_IMAGE,
            "-i",
            AUDIO_FILE,
            "-c:v",
            "libx264",
            "-tune",
            "stillimage",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-pix_fmt",
            "yuv420p",
            "-shortest",
            VIDEO_FILE,
        ],
        check=True,
    )

# -------------------------
# UPLOAD TO YOUTUBE
# -------------------------
def upload_video(title, description):
    creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    youtube = build("youtube", "v3", credentials=creds)

    request_body = {
        "snippet": {
            "title": title[:95],
            "description": description,
            "categoryId": "27",
        },
        "status": {"privacyStatus": "public"},
    }

    media = MediaFileUpload(VIDEO_FILE, resumable=True)

    request = youtube.videos().insert(
        part="snippet,status",
        body=request_body,
        media_body=media,
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Upload progress: {int(status.progress() * 100)}%")

    print("VIDEO UPLOADED:", response["id"])

# -------------------------
# MAIN PIPELINE
# -------------------------
def main():
    print("Starting auto video pipeline...")

    category, topic = pick_topic()
    print("Topic:", topic)

    script = generate_script(category, topic)

    generate_voice(script)
    create_video()

    today = datetime.utcnow().strftime("%Y-%m-%d")
    title = f"{topic} | AI Explained"
    description = script

    upload_video(title, description)

    print("DONE.")

if __name__ == "__main__":
    main()