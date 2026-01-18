import os
import subprocess
import random
import requests
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
    "How ancient Egyptians built pyramids",
    "Secrets of the Roman Empire",
    "The mystery of Stonehenge"
]

# ----------------------------------------


def generate_script(category, topic):
    return f"""
Welcome to today's documentary.

Today we explore {topic}, one of the most fascinating subjects in {category}.

The origins of {topic} date back thousands of years.
Historians believe it played a major role in shaping civilization.

Archaeological discoveries reveal advanced engineering,
careful urban planning, and a deep understanding of science.

Many mysteries about {topic} remain unsolved.
Researchers continue to debate how ancient people achieved such feats.

Understanding {topic} helps us understand humanity itself.

Subscribe for more history and technology documentaries.
"""


def generate_voice(text):
    with open("script.txt", "w") as f:
        f.write(text)

    subprocess.run([
        "edge-tts",
        "--voice", "en-US-GuyNeural",
        "--rate", "+0%",
        "--text", text,
        "--write-media", VOICE_FILE
    ], check=True)


def download_images(topic):
    os.makedirs(IMAGE_DIR, exist_ok=True)
    images_downloaded = 0

    search_url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": topic,
        "gsrlimit": 5,
        "prop": "pageimages",
        "piprop": "original"
    }

    r = requests.get(search_url, params=params).json()
    pages = r.get("query", {}).get("pages", {})

    for i, page in enumerate(pages.values()):
        if "original" in page:
            img_url = page["original"]["source"]
            img_path = f"{IMAGE_DIR}/img_{i:02d}.jpg"
            img_data = requests.get(img_url).content
            with open(img_path, "wb") as f:
                f.write(img_data)
            images_downloaded += 1

    if images_downloaded == 0:
        create_fallback_images()


def create_fallback_images():
    os.makedirs(IMAGE_DIR, exist_ok=True)
    for i in range(5):
        subprocess.run([
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", "color=c=darkslategray:s=1280x720",
            "-frames:v", "1",
            f"{IMAGE_DIR}/img_{i:02d}.jpg"
        ], check=True)


def create_video():
    subprocess.run([
        "ffmpeg", "-y",
        "-r", "1/5",
        "-i", f"{IMAGE_DIR}/img_%02d.jpg",
        "-i", VOICE_FILE,
        "-vf",
        "zoompan=z='min(zoom+0.0015,1.1)':d=125:s=1280x720",
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
                "tags": ["history", "documentary", "education"],
                "categoryId": "27"
            },
            "status": {
                "privacyStatus": "public"
            }
        },
        media_body=MediaFileUpload(VIDEO_FILE, resumable=True)
    )

    response = request.execute()
    print("Uploaded:", response["id"])


def main():
    print("Starting auto video pipeline...")

    topic = random.choice(TOPICS)
    print("Topic:", topic)

    script = generate_script(CATEGORY, topic)
    generate_voice(script)

    download_images(topic)
    create_video()

    upload_video(
        title=topic,
        description=script
    )


if __name__ == "__main__":
    main()