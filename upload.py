import os
import subprocess
import textwrap
import random
import time
import requests
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

# ================= CONFIG =================
VOICE = "en-IN-PrabhatNeural"
IMAGE_COUNT = 40               # More images = longer video
IMAGE_DURATION = 8             # seconds per image
FPS = 30
VIDEO_SIZE = "1280x720"
TOPIC_FILE = "topic.txt"
# ==========================================

def get_topic():
    if os.path.exists(TOPIC_FILE):
        return open(TOPIC_FILE).read().strip()
    return random.choice([
        "How ancient Egyptians built pyramids",
        "Secrets of the Roman Colosseum",
        "The mystery of Stonehenge",
        "How Vikings navigated the oceans"
    ])

def generate_script(topic):
    print("Generating script...")
    paragraphs = []
    for i in range(20):  # makes long narration
        paragraphs.append(
            f"{topic}. This section explains the historical background, "
            f"scientific theories, cultural importance, and expert analysis "
            f"in simple language for viewers."
        )
    script = "\n\n".join(paragraphs)
    open("script.txt", "w").write(script)
    return script

def generate_voice():
    print("Generating voice...")
    subprocess.run([
        "edge-tts",
        "--voice", VOICE,
        "--file", "script.txt",
        "--write-media", "voice.mp3"
    ], check=True)

def download_images(topic):
    print("Downloading images...")
    os.makedirs("images", exist_ok=True)
    downloaded = 0

    for i in range(IMAGE_COUNT * 2):
        url = f"https://source.unsplash.com/1600x900/?{topic.replace(' ', ',')}"
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                img_path = f"images/img_{downloaded}.jpg"
                open(img_path, "wb").write(r.content)
                downloaded += 1
        except:
            pass

        if downloaded >= IMAGE_COUNT:
            break

    if downloaded == 0:
        raise RuntimeError("No images downloaded")

def create_video():
    print("Creating animated video...")
    with open("list.txt", "w") as f:
        for img in sorted(os.listdir("images")):
            f.write(f"file 'images/{img}'\n")
            f.write(f"duration {IMAGE_DURATION}\n")

    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", "list.txt",
        "-vf",
        f"scale={VIDEO_SIZE},zoompan=z='zoom+0.0005':d={IMAGE_DURATION*FPS}",
        "-pix_fmt", "yuv420p",
        "video.mp4"
    ], check=True)

def merge_audio():
    print("Merging audio...")
    subprocess.run([
        "ffmpeg", "-y",
        "-i", "video.mp4",
        "-i", "voice.mp3",
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        "final.mp4"
    ], check=True)

def upload_to_youtube(topic):
    print("Uploading to YouTube...")
    creds = Credentials.from_authorized_user_file("token.json", [
        "https://www.googleapis.com/auth/youtube.upload"
    ])

    youtube = build("youtube", "v3", credentials=creds)

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": topic,
                "description": topic + "\n\nAuto-generated educational video.",
                "tags": ["history", "education", "facts"],
                "categoryId": "27"
            },
            "status": {
                "privacyStatus": "public"
            }
        },
        media_body=MediaFileUpload("final.mp4")
    )

    request.execute()
    print("Upload complete!")

def main():
    print("Starting auto video pipeline...")
    topic = get_topic()
    print("Topic:", topic)

    generate_script(topic)
    generate_voice()
    download_images(topic)
    create_video()
    merge_audio()
    upload_to_youtube(topic)

if __name__ == "__main__":
    main()