import os
import subprocess
import random
import requests
import json
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

# ---------------- CONFIG ----------------

VIDEO_FILE = "output.mp4"
VOICE_FILE = "voice.mp3"
IMAGE_DIR = "images"

CATEGORY = "History"
TOPICS = [
    "The lost city of Mohenjo-daro",
    "The mystery of Stonehenge",
    "Secrets of the Roman Empire",
    "How ancient Egyptians built pyramids"
]

# ----------------------------------------


def generate_script(category, topic):
    return f"""
Welcome to today's documentary.

Today we explore {topic}, one of the most fascinating mysteries in {category}.

Archaeologists believe this site was built thousands of years ago.
The engineering techniques used still puzzle modern scientists.

Massive structures were created without modern tools.
Many theories exist, from religious rituals to astronomical purposes.

Despite decades of research, many secrets remain hidden.
New discoveries continue to reshape our understanding.

If you enjoy deep history and ancient mysteries,
subscribe for more documentaries like this.
"""


def generate_voice(text):
    subprocess.run([
        "edge-tts",
        "--voice", "en-US-GuyNeural",
        "--rate", "+0%",
        "--text", text,
        "--write-media", VOICE_FILE
    ], check=True)


def safe_json(response):
    try:
        return response.json()
    except Exception:
        return None


def download_images(topic):
    os.makedirs(IMAGE_DIR, exist_ok=True)
    downloaded = 0

    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": topic,
        "gsrlimit": 6,
        "prop": "pageimages",
        "piprop": "original"
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        data = safe_json(resp)
        if not data:
            raise ValueError("No JSON")

        pages = data.get("query", {}).get("pages", {})
        for i, page in enumerate(pages.values()):
            if "original" in page:
                img_url = page["original"]["source"]
                img_data = requests.get(img_url, timeout=10).content
                with open(f"{IMAGE_DIR}/img_{i:02d}.jpg", "wb") as f:
                    f.write(img_data)
                downloaded += 1

    except Exception:
        downloaded = 0

    if downloaded < 3:
        print("No usable images — using fallback")
        create_fallback_images()


def create_fallback_images():
    os.makedirs(IMAGE_DIR, exist_ok=True)
    for i in range(6):
        subprocess.run([
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", "color=c=darkslategray:s=1280x720",
            "-frames:v", "1",
            f"{IMAGE_DIR}/img_{i:02d}.jpg"
        ], check=True)


def get_audio_duration():
    result = subprocess.check_output([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        VOICE_FILE
    ])
    return float(result.strip())


def create_video():
    duration = get_audio_duration()
    img_duration = duration / 6

    subprocess.run([
        "ffmpeg", "-y",
        "-framerate", f"1/{img_duration}",
        "-i", f"{IMAGE_DIR}/img_%02d.jpg",
        "-i", VOICE_FILE,
        "-vf",
        "zoompan=z='min(zoom+0.002,1.15)':d=125:s=1280x720",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-shortest",
        VIDEO_FILE
    ], check=True)


def upload_video(title, description):
    creds = Credentials.from_authorized_user_file("token.json")
    youtube = build("youtube", "v3", credentials=creds)

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": title,
                "description": description,
                "tags": ["history", "documentary", "ancient"],
                "categoryId": "27"
            },
            "status": {
                "privacyStatus": "public"
            }
        },
        media_body=MediaFileUpload(VIDEO_FILE, resumable=True)
    )

    response = request.execute()
    print("Uploaded video ID:", response["id"])


def main():
    print("Starting auto video pipeline...")

    topic = random.choice(TOPICS)
    print("Topic:", topic)

    script = generate_script(CATEGORY, topic)
    generate_voice(script)

    download_images(topic)
    create_video()

    upload_video(topic, script)


if __name__ == "__main__":
    main()