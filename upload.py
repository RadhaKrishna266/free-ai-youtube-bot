import os
import random
import subprocess
import requests
from datetime import datetime

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

TOKEN_PATH = "token.json"
AUDIO_FILE = "voice.mp3"
VIDEO_FILE = "output.mp4"
IMG_DIR = "images"

# -------------------------
# PICK TOPIC
# -------------------------
def pick_topic():
    category = random.choice(["history", "tech"])
    with open(f"topics/{category}.txt", "r", encoding="utf-8") as f:
        topics = [t.strip() for t in f if t.strip()]
    return category, random.choice(topics)

# -------------------------
# SCRIPT
# -------------------------
def generate_script(category, topic):
    if category == "history":
        return (
            f"{topic}. This ancient civilization was far ahead of its time. "
            "Its discoveries still surprise historians today."
        )
    else:
        return (
            f"{topic} explained simply. This technology impacts your daily life "
            "more than you realize."
        )

# -------------------------
# VOICE
# -------------------------
def generate_voice(text):
    subprocess.run(
        ["python", "-m", "edge_tts", "--voice", "en-US-GuyNeural",
         "--text", text, "--write-media", AUDIO_FILE],
        check=True
    )
def create_fallback_images():
    os.makedirs(IMG_DIR, exist_ok=True)
    for i in range(5):
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f", "lavfi",
                "-i", "color=c=darkslategray:s=1280x720",
                "-frames:v", "1",
                f"{IMG_DIR}/img{i}.jpg",
            ],
            check=True,
        )

# -------------------------
# DOWNLOAD WIKIMEDIA IMAGES
# -------------------------
def download_images(topic):
    os.makedirs(IMG_DIR, exist_ok=True)

    headers = {
        "User-Agent": "free-ai-youtube-bot/1.0"
    }

    search = topic.replace(" ", "_")
    url = (
        "https://commons.wikimedia.org/w/api.php"
        "?action=query"
        "&generator=search"
        f"&gsrsearch={search}"
        "&gsrlimit=10"
        "&prop=imageinfo"
        "&iiprop=url"
        "&format=json"
    )

    try:
        r = requests.get(url, headers=headers, timeout=20)
        data = r.json()
    except Exception:
        print("Wikimedia failed — using fallback images")
        create_fallback_images()
        return

    pages = data.get("query", {}).get("pages", {})

    saved = 0
    for page in pages.values():
        if "imageinfo" not in page:
            continue

        img_url = page["imageinfo"][0].get("url")
        if not img_url:
            continue

        try:
            img_data = requests.get(img_url, headers=headers, timeout=20).content
            with open(f"{IMG_DIR}/img{saved}.jpg", "wb") as f:
                f.write(img_data)
            saved += 1
        except Exception:
            continue

        if saved >= 5:
            break

    if saved == 0:
        print("No usable images — using fallback")
        create_fallback_images()

# -------------------------
# CREATE ANIMATED VIDEO
# -------------------------
def create_video():
    images = sorted([f"{IMG_DIR}/{f}" for f in os.listdir(IMG_DIR)])
    with open("list.txt", "w") as f:
        for img in images:
            f.write(f"file '{img}'\n")
            f.write("duration 3\n")

    subprocess.run(
        [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", "list.txt",
            "-i", AUDIO_FILE,
            "-vf", "zoompan=z='min(zoom+0.0015,1.2)':d=90",
            "-pix_fmt", "yuv420p",
            "-shortest",
            VIDEO_FILE
        ],
        check=True
    )

# -------------------------
# UPLOAD
# -------------------------
def upload_video(title, description):
    creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    youtube = build("youtube", "v3", credentials=creds)

    body = {
        "snippet": {
            "title": title[:95],
            "description": description,
            "categoryId": "27"
        },
        "status": {"privacyStatus": "public"}
    }

    media = MediaFileUpload(VIDEO_FILE, resumable=True)
    request = youtube.videos().insert(
        part="snippet,status", body=body, media_body=media
    )

    while True:
        status, response = request.next_chunk()
        if response:
            print("UPLOADED:", response["id"])
            break

# -------------------------
# MAIN
# -------------------------
def main():
    category, topic = pick_topic()
    script = generate_script(category, topic)

    generate_voice(script)
    download_images(topic)
    create_video()

    upload_video(
        f"{topic} | Explained",
        script
    )

if __name__ == "__main__":
    main()

def create_fallback_images():
    for i in range(5):
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f", "lavfi",
                "-i", "color=c=darkslategray:s=1280x720",
                "-frames:v", "1",
                f"{IMG_DIR}/img{i}.jpg",
            ],
            check=True,
        )