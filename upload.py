import os
import json
import base64
import subprocess
import requests
from gtts import gTTS
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

PIXABAY_KEY = os.environ["PIXABAY_API_KEY"]

TOPIC = "unknown science facts"
FACTS = [
    "Octopuses have three hearts",
    "Honey never spoils",
    "Sharks existed before trees",
    "Bananas are berries",
    "Wombat poop is cube shaped"
]

IMG_DIR = "images"
os.makedirs(IMG_DIR, exist_ok=True)


def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)


# 🖼️ DOWNLOAD REAL IMAGES
def download_images():
    print("🖼️ Downloading images from Pixabay")
    for i, fact in enumerate(FACTS):
        query = fact.split()[0]
        url = (
            f"https://pixabay.com/api/?key={PIXABAY_KEY}"
            f"&q={query}&image_type=photo&per_page=3"
        )
        r = requests.get(url).json()
        img_url = r["hits"][0]["largeImageURL"]
        img_data = requests.get(img_url).content

        with open(f"{IMG_DIR}/{i}.jpg", "wb") as f:
            f.write(img_data)

    print("✅ Images downloaded")


# 🔊 VOICE (CLEAR)
def create_voice():
    text = "Unknown facts you never knew. " + ". ".join(FACTS)
    gTTS(text=text, lang="en", slow=False).save("voice.mp3")
    print("✅ voice.mp3 created")


# 🎬 ANIMATED VIDEO
def create_video():
    inputs = []
    filters = []

    for i in range(len(FACTS)):
        inputs.extend(["-loop", "1", "-t", "6", "-i", f"{IMG_DIR}/{i}.jpg"])
        filters.append(
            f"[{i}:v]scale=1280:720,zoompan=z='min(zoom+0.0008,1.2)':d=180,fade=t=in:st=0:d=0.5,fade=t=out:st=5:d=0.5[v{i}]"
        )

    concat = "".join([f"[v{i}]" for i in range(len(FACTS))])
    filters.append(f"{concat}concat=n={len(FACTS)}:v=1:a=0[outv]")

    filter_complex = ";".join(filters)

    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-i", "voice.mp3",
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-map", "audio",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-shortest",
        "final.mp4"
    ]

    run(cmd)
    print("✅ final.mp4 created (REAL IMAGES + ANIMATION + VOICE)")


# 🔐 YOUTUBE AUTH
def youtube_auth():
    token = base64.b64decode(os.environ["YOUTUBE_TOKEN_BASE64"]).decode()
    creds = Credentials.from_authorized_user_info(
        json.loads(token),
        ["https://www.googleapis.com/auth/youtube.upload"]
    )
    return build("youtube", "v3", credentials=creds)


# 🚀 SINGLE UPLOAD (NO DUPLICATE)
def upload():
    yt = youtube_auth()

    request = yt.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": "Unknown Facts You Never Knew",
                "description": "AI animated video with real images and voice",
                "tags": ["facts", "unknown facts", "science"],
                "categoryId": "27"
            },
            "status": {"privacyStatus": "public"}
        },
        media_body=MediaFileUpload(
            "final.mp4",
            mimetype="video/mp4",
            resumable=False
        )
    )

    response = request.execute()
    print("✅ Uploaded video ID:", response["id"])


def main():
    download_images()
    create_voice()
    create_video()
    upload()


if __name__ == "__main__":
    main()