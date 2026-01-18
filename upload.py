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
IMAGE_COUNT = 15
IMAGE_DURATION = 8  # seconds per image
VIDEO_RES = "1280x720"
# --------------------------------------


def generate_script(topic):
    sections = [
        "Introduction",
        "Historical Background",
        "Discovery",
        "Construction Techniques",
        "Cultural Importance",
        "Scientific Theories",
        "Unsolved Mysteries",
        "Modern Research",
        "Why It Still Fascinates Us",
        "Conclusion"
    ]

    script = ""
    for sec in sections:
        script += f"\n{sec}.\n"
        script += textwrap.fill(
            f"{topic} has fascinated historians and scientists for generations. "
            "This section explores the subject in depth, explaining facts, theories, "
            "and discoveries in a clear and engaging way. "
            "Each detail helps us better understand how advanced ancient civilizations truly were. "
            "Even today, researchers continue to uncover surprising insights.",
            80
        ) + "\n\n"

    return script.strip()


def generate_voice(script):
    with open("script.txt", "w", encoding="utf-8") as f:
        f.write(script)

    subprocess.run([
        "edge-tts",
        "-f", "script.txt",
        "--voice", VOICE,
        "--write-media", "voice.mp3"
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
            img_path = f"images/img_{len(images)}.jpg"
            with open(img_path, "wb") as f:
                f.write(requests.get(img_url).content)
            images.append(img_path)

    if not images:
        raise Exception("No images downloaded")

    return images


def create_video(images):
    with open("images.txt", "w") as f:
        for img in images:
            f.write(f"file '{img}'\n")
            f.write(f"duration {IMAGE_DURATION}\n")

    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", "images.txt",
        "-i", "voice.mp3",
        "-vf",
        "scale=1280:720,zoompan=z='min(zoom+0.0004,1.15)':d=200",
        "-pix_fmt", "yuv420p",
        "-shortest",
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
        media_body=MediaFileUpload("output.mp4", resumable=True)
    )

    request.execute()


def main():
    topic = random.choice([
        "The mystery of Stonehenge",
        "How ancient Egyptians built pyramids",
        "The lost city of Mohenjo-daro",
        "Secrets of the Roman Colosseum"
    ])

    print("Starting auto video pipeline...")
    print("Topic:", topic)

    script = generate_script(topic)
    generate_voice(script)

    images = download_images(topic)
    create_video(images)

    upload_video(topic, script[:4500])


if __name__ == "__main__":
    main()