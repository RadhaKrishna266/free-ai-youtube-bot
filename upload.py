import os
import json
import base64
import subprocess
import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

PIXABAY_KEY = os.environ["PIXABAY_API_KEY"]
IMAGE_COUNT = 10
IMAGE_DURATION = 6
TOTAL_DURATION = IMAGE_COUNT * IMAGE_DURATION


def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)


# 🔊 AUDIO
def create_audio():
    run([
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "sine=frequency=440",
        "-t", str(TOTAL_DURATION),
        "-c:a", "aac",
        "-b:a", "128k",
        "voice.m4a"
    ])
    print("✅ Audio created")


# 🖼️ IMAGES
def download_images():
    os.makedirs("images", exist_ok=True)

    url = (
        f"https://pixabay.com/api/?key={PIXABAY_KEY}"
        "&q=human+face+portrait"
        "&image_type=photo&per_page=20"
    )

    data = requests.get(url).json()
    hits = data["hits"][:IMAGE_COUNT]

    for i, img in enumerate(hits):
        img_data = requests.get(img["largeImageURL"]).content
        with open(f"images/{i:03d}.jpg", "wb") as f:
            f.write(img_data)

    print("✅ Images downloaded")


# 🎬 VIDEO (SAFE ANIMATION)
def create_video():
    run([
        "ffmpeg", "-y",
        "-framerate", f"1/{IMAGE_DURATION}",
        "-i", "images/%03d.jpg",
        "-i", "voice.m4a",
        "-vf",
        (
            "scale=1280:720:force_original_aspect_ratio=decrease,"
            "pad=1280:720:(ow-iw)/2:(oh-ih)/2,"
            "zoompan=z='if(lte(zoom,1.0),1.0,zoom-0.0005)':d=150"
        ),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-shortest",
        "final.mp4"
    ])

    print("✅ Animated video created")


# 🔐 YOUTUBE AUTH
def youtube_service():
    token = json.loads(
        base64.b64decode(os.environ["YOUTUBE_TOKEN_BASE64"]).decode()
    )

    creds = Credentials.from_authorized_user_info(
        token,
        ["https://www.googleapis.com/auth/youtube.upload"]
    )

    return build("youtube", "v3", credentials=creds)


# 🚀 UPLOAD (ONCE)
def upload():
    yt = youtube_service()

    request = yt.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": "Unknown Human Facts You Never Knew",
                "description": "Animated AI facts video with real images",
                "tags": ["facts", "human psychology", "unknown facts"],
                "categoryId": "27"
            },
            "status": {"privacyStatus": "public"}
        },
        media_body=MediaFileUpload("final.mp4", resumable=False)
    )

    res = request.execute()
    print("✅ Uploaded:", res["id"])


def main():
    print("🚀 Starting stable animated video pipeline")
    create_audio()
    download_images()
    create_video()
    upload()


if __name__ == "__main__":
    main()