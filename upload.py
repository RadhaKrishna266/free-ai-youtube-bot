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
def generate_script(topic):
    return f"""
Here are some amazing facts about {topic}.

{topic} has a fascinating history that most people don't know.
It played an important role in shaping the modern world.

One interesting fact is that {topic} changed how humans think and work.
Another surprising detail is how {topic} evolved over time.

Experts believe {topic} will become even more important in the future.
This is why understanding {topic} is useful for everyone.

Thanks for watching. Subscribe for more amazing facts.
"""

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
    os.system("""
ffmpeg -y -r 1/5 -i images/img_%02d.jpg -i voice.mp3 \
-vf "zoompan=z='min(zoom+0.0008,1.08)':d=125:s=1280x720" \
-c:v libx264 -pix_fmt yuv420p -shortest output.mp4
""")

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