import os
import random
import subprocess
import requests
import json
import time

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

# ================= CONFIG =================
TOPICS = [
    "The mystery of Stonehenge",
    "How ancient Egyptians built pyramids",
    "Secrets of the Roman Colosseum",
    "How Vikings navigated the oceans"
]

VOICE_FILE = "voice.mp3"
VIDEO_FILE = "video.mp4"
IMAGE_DIR = "images"
TOKEN_FILE = "token.json"

# ==========================================


def generate_script(topic):
    return f"""
{topic} has fascinated historians for centuries.

In this video, we explore how it was created, why it mattered,
and what mysteries still remain today.

Experts believe advanced planning, engineering, and teamwork
played a major role in its construction.

Despite modern technology, many details remain unexplained,
making it one of history’s greatest wonders.
"""


def generate_voice(text):
    subprocess.run([
        "edge-tts",
        "--voice", "en-US-AriaNeural",
        "--text", text,
        "--write-media", VOICE_FILE
    ], check=True)


def get_audio_duration():
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration", "-of",
         "default=noprint_wrappers=1:nokey=1", VOICE_FILE],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    return float(result.stdout.strip())


def download_images(topic):
    os.makedirs(IMAGE_DIR, exist_ok=True)

    headers = {"User-Agent": "Mozilla/5.0"}
    query = topic.replace(" ", "+")
    url = f"https://www.bing.com/images/search?q={query}&form=HDRSC2"

    print("Downloading images from Bing...")
    html = requests.get(url, headers=headers, timeout=10).text

    links = []
    for part in html.split("murl&quot;:&quot;")[1:]:
        link = part.split("&quot;")[0]
        if link.startswith("http"):
            links.append(link)

    links = links[:6]

    if len(links) < 3:
        print("Not enough images, using fallback")
        create_fallback_images()
        return

    for i, img_url in enumerate(links):
        try:
            img = requests.get(img_url, headers=headers, timeout=10).content
            with open(f"{IMAGE_DIR}/img_{i:02d}.jpg", "wb") as f:
                f.write(img)
            print(f"Saved img_{i:02d}.jpg")
        except:
            pass


def create_fallback_images():
    os.makedirs(IMAGE_DIR, exist_ok=True)
    for i in range(6):
        subprocess.run([
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"color=c=blue:s=1280x720:d=5",
            f"{IMAGE_DIR}/img_{i:02d}.jpg"
        ])


def create_video():
    duration = get_audio_duration()
    images = sorted(os.listdir(IMAGE_DIR))
    img_duration = duration / len(images)

    subprocess.run([
        "ffmpeg", "-y",
        "-framerate", f"1/{img_duration}",
        "-i", f"{IMAGE_DIR}/img_%02d.jpg",
        "-i", VOICE_FILE,
        "-vf",
        "zoompan=z='if(lte(zoom,1.0),1.1,zoom+0.0015)':"
        "x='iw/2-(iw/zoom/2)':"
        "y='ih/2-(ih/zoom/2)':"
        "d=125:s=1280x720",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-shortest",
        VIDEO_FILE
    ], check=True)


def upload_to_youtube(title, description):
    creds = Credentials.from_authorized_user_file(
        TOKEN_FILE,
        ["https://www.googleapis.com/auth/youtube.upload"]
    )

    youtube = build("youtube", "v3", credentials=creds)

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": title,
                "description": description,
                "categoryId": "27"
            },
            "status": {
                "privacyStatus": "public"
            }
        },
        media_body=MediaFileUpload(VIDEO_FILE)
    )

    response = request.execute()
    print("Uploaded:", response["id"])


def clean():
    for f in [VOICE_FILE, VIDEO_FILE]:
        if os.path.exists(f):
            os.remove(f)
    if os.path.exists(IMAGE_DIR):
        for f in os.listdir(IMAGE_DIR):
            os.remove(os.path.join(IMAGE_DIR, f))


def main():
    print("Starting auto video pipeline...")

    topic = random.choice(TOPICS)
    print("Topic:", topic)

    script = generate_script(topic)
    generate_voice(script)
    download_images(topic)
    create_video()
    upload_to_youtube(topic, script)

    clean()


if __name__ == "__main__":
    main()