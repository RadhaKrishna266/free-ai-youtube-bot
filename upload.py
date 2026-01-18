import os
import subprocess
import textwrap
import requests
import random
from PIL import Image
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

# ================= CONFIG =================
TOPICS = [
    "How ancient Egyptians built pyramids",
    "Secrets of the Roman Colosseum",
    "Mystery of Stonehenge",
]

VOICE = "en-IN-PrabhatNeural"
MIN_IMAGES = 25
VIDEO_SIZE = "1920:1080"
SCRIPT_WORDS = 1200  # ~8–10 minutes
BG_MUSIC = "music.mp3"

# ==========================================

def clean():
    for f in os.listdir():
        if f.startswith(("img_", "part_", "audio_")):
            os.remove(f)

def generate_script(topic):
    print("Generating long script...")
    paragraphs = []
    for i in range(10):
        paragraphs.append(
            f"{topic} section {i+1}. "
            f"This section explains historical context, facts, theories, and mysteries in detail. "
            f"It provides clear explanations, examples, and storytelling to engage viewers."
        )
    script = " ".join(paragraphs)
    script = " ".join(script.split()[:SCRIPT_WORDS])
    with open("script.txt", "w", encoding="utf-8") as f:
        f.write(script)
    return script

def generate_voice():
    print("Generating voice safely...")
    with open("script.txt", "r", encoding="utf-8") as f:
        text = f.read()

    chunks = textwrap.wrap(text, 4000)
    audio_files = []

    for i, chunk in enumerate(chunks):
        part = f"audio_{i}.mp3"
        subprocess.run([
            "edge-tts",
            "--voice", VOICE,
            "--text", chunk,
            "--write-media", part
        ], check=True)
        audio_files.append(part)

    with open("audio_list.txt", "w") as f:
        for a in audio_files:
            f.write(f"file '{a}'\n")

    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", "audio_list.txt",
        "-c", "copy",
        "voice.mp3"
    ], check=True)

def download_images(topic):
    print("Downloading images...")
    os.makedirs("images", exist_ok=True)
    urls = [
        f"https://source.unsplash.com/1600x900/?{topic.replace(' ','-')}",
        f"https://source.unsplash.com/1600x900/?history",
        f"https://source.unsplash.com/1600x900/?ancient",
    ]

    images = []
    for i in range(MIN_IMAGES):
        url = random.choice(urls)
        path = f"img_{i}.jpg"
        r = requests.get(url, timeout=20)
        with open(path, "wb") as f:
            f.write(r.content)
        try:
            img = Image.open(path).convert("RGB")
            img.save(path, "JPEG", quality=95)
            images.append(path)
        except:
            os.remove(path)

    if len(images) < MIN_IMAGES:
        images *= (MIN_IMAGES // len(images) + 1)

    return images[:MIN_IMAGES]

def create_video(images):
    print("Creating animated video...")
    with open("images.txt", "w") as f:
        for img in images:
            f.write(f"file '{img}'\n")
            f.write("duration 5\n")

    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", "images.txt",
        "-i", "voice.mp3",
        "-stream_loop", "-1",
        "-i", BG_MUSIC,
        "-filter_complex",
        f"[0:v]scale={VIDEO_SIZE},zoompan=z='min(zoom+0.0005,1.2)':d=125:s={VIDEO_SIZE}[v];"
        "[2:a]volume=0.05[a2]",
        "-map", "[v]",
        "-map", "1:a",
        "-map", "[a2]",
        "-shortest",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "final_video.mp4"
    ], check=True)

def upload_youtube():
    print("Uploading to YouTube...")
    creds = Credentials.from_authorized_user_file("token.json", ["https://www.googleapis.com/auth/youtube.upload"])
    youtube = build("youtube", "v3", credentials=creds)

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": "Ancient History Explained",
                "description": "AI generated documentary",
                "tags": ["history", "ancient", "documentary"],
                "categoryId": "27"
            },
            "status": {
                "privacyStatus": "public"
            }
        },
        media_body=MediaFileUpload("final_video.mp4")
    )
    request.execute()

def main():
    clean()
    topic = random.choice(TOPICS)
    print("Topic:", topic)

    generate_script(topic)
    generate_voice()
    images = download_images(topic)
    create_video(images)
    upload_youtube()

    print("DONE ✅")

if __name__ == "__main__":
    main()