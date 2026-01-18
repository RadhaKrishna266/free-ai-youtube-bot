import os
import random
import subprocess
import requests
import textwrap
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

# ---------------- CONFIG ----------------
VOICE = "en-IN-PrabhatNeural"
IMAGE_COUNT = 12
VIDEO_RES = "1280x720"

# ----------------------------------------

def generate_script(topic):
    sections = [
        "Introduction",
        "Historical background",
        "How it was discovered",
        "How it was built",
        "Why it was important",
        "Scientific theories",
        "Unsolved mysteries",
        "Modern research",
        "Why it still fascinates people",
        "Conclusion"
    ]

    script = ""
    for sec in sections:
        script += f"""
{sec}.

{textwrap.fill(
f"This section explains {topic.lower()} in detail. "
"Experts have studied this topic for many decades. "
"It reveals advanced knowledge, planning, and deep cultural meaning. "
"New discoveries continue to surprise historians and scientists.",
80)}
"""

    return script.strip()


def generate_voice(script):
    with open("script.txt", "w", encoding="utf-8") as f:
        f.write(script)

    subprocess.run([
        "edge-tts",
        "--voice", VOICE,
        "--input", "script.txt",
        "--output", "voice.mp3"
    ], check=True)


def download_images(topic):
    os.makedirs("images", exist_ok=True)

    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": topic,
        "gsrlimit": IMAGE_COUNT,
        "prop": "pageimages",
        "piprop": "original",
        "format": "json"
    }

    r = requests.get(url, params=params).json()
    pages = r.get("query", {}).get("pages", {})

    images = []
    for page in pages.values():
        if "original" in page:
            img_url = page["original"]["source"]
            img_name = f"images/{len(images)}.jpg"
            img = requests.get(img_url).content
            with open(img_name, "wb") as f:
                f.write(img)
            images.append(img_name)

    if not images:
        raise Exception("No images found")

    return images


def create_video(images):
    with open("images.txt", "w") as f:
        for img in images:
            f.write(f"file '{img}'\nduration 6\n")

    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", "images.txt",
        "-vf", "scale=1280:720,zoompan=z='min(zoom+0.0005,1.1)':d=150",
        "-i", "voice.mp3",
        "-shortest",
        "-pix_fmt", "yuv420p",
        "output.mp4"
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
                "categoryId": "27"
            },
            "status": {
                "privacyStatus": "public"
            }
        },
        media_body=MediaFileUpload("output.mp4")
    )

    request.execute()


def main():
    topic = random.choice([
        "The mystery of Stonehenge",
        "How ancient Egyptians built pyramids",
        "The lost city of Mohenjo-daro",
        "Secrets of the Roman Colosseum"
    ])

    print("Topic:", topic)

    script = generate_script(topic)
    generate_voice(script)

    images = download_images(topic)
    create_video(images)

    upload_video(
        title=topic,
        description=script[:4000]
    )


if __name__ == "__main__":
    main()