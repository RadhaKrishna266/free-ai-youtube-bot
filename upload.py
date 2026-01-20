import os
import random
import subprocess
import requests
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

# ---------------- CONFIG ----------------
VIDEO_FILE = "final.mp4"
AUDIO_FILE = "voice.m4a"
IMAGES_DIR = "images"
FACTS_FILE = "facts.txt"

PIXABAY_KEY = os.environ.get("PIXABAY_API_KEY")
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")

# ---------------------------------------

def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)

# ---------- FACT GENERATION ----------
def generate_facts(count=10):
    pool = [
        "The human face has over 40 muscles.",
        "No two human faces are exactly the same.",
        "People recognize faces faster than objects.",
        "Your face keeps changing as you age.",
        "Smiling uses fewer muscles than frowning.",
        "Faces are processed by a special brain area.",
        "Identical twins still have different faces.",
        "Your face is most recognizable in motion.",
        "Humans detect faces in under 100 milliseconds.",
        "Babies recognize faces before words."
    ]

    facts = random.sample(pool, count)

    with open(FACTS_FILE, "w") as f:
        for i, fact in enumerate(facts, 1):
            f.write(f"{i}. {fact}\n")

    print("✅ Facts generated")
    return facts

# ---------- AUDIO ----------
def create_audio():
    run([
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "sine=frequency=440",
        "-t", "60",
        "-c:a", "aac",
        "-b:a", "128k",
        AUDIO_FILE
    ])
    print("✅ Audio created")

# ---------- IMAGES ----------
def download_images(query="human face", count=10):
    os.makedirs(IMAGES_DIR, exist_ok=True)

    url = "https://pixabay.com/api/"
    params = {
        "key": PIXABAY_KEY,
        "q": query,
        "image_type": "photo",
        "orientation": "vertical",
        "per_page": count,
        "safesearch": "true"
    }

    r = requests.get(url, params=params).json()
    hits = r.get("hits", [])

    for i, hit in enumerate(hits[:count]):
        img = requests.get(hit["largeImageURL"]).content
        with open(f"{IMAGES_DIR}/{i:03d}.jpg", "wb") as f:
            f.write(img)

    print("✅ Images downloaded")

# ---------- VIDEO ----------
def create_video():
    run([
        "ffmpeg", "-y",
        "-framerate", "1/6",
        "-i", f"{IMAGES_DIR}/%03d.jpg",
        "-i", AUDIO_FILE,
        "-vf",
        "scale=1280:720:force_original_aspect_ratio=decrease,"
        "pad=1280:720:(ow-iw)/2:(oh-ih)/2,"
        "zoompan=z='min(zoom+0.0006,1.15)':d=150",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-shortest",
        VIDEO_FILE
    ])
    print("✅ Animated video created")

# ---------- UPLOAD ----------
def upload(facts):
    creds = Credentials.from_authorized_user_file("token.json")
    youtube = build("youtube", "v3", credentials=creds)

    title = facts[0][:95]
    description = "\n".join(facts)

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": title,
                "description": description,
                "tags": ["facts", "face facts", "ai video"],
                "categoryId": "22"
            },
            "status": {
                "privacyStatus": "public"
            }
        },
        media_body=MediaFileUpload(VIDEO_FILE, resumable=True)
    )

    response = request.execute()
    print("✅ Uploaded video ID:", response["id"])

# ---------- MAIN ----------
def main():
    print("🚀 Starting stable animated video pipeline")
    facts = generate_facts()
    create_audio()
    download_images()
    create_video()
    upload(facts)

if __name__ == "__main__":
    main()