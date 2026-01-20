import os
import base64
import json
import subprocess
import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

DURATION_PER_IMAGE = 6
IMAGE_COUNT = 10
TOTAL_DURATION = DURATION_PER_IMAGE * IMAGE_COUNT

PIXABAY_KEY = os.environ["PIXABAY_API_KEY"]


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
        "voice.m4a"
    ])
    print("✅ Audio created")


# 🖼️ DOWNLOAD FACE IMAGES
def download_images():
    os.makedirs("images", exist_ok=True)

    query = "human face portrait"
    url = (
        f"https://pixabay.com/api/?key={PIXABAY_KEY}"
        f"&q={query}&image_type=photo&per_page={IMAGE_COUNT}"
    )

    data = requests.get(url).json()
    hits = data["hits"][:IMAGE_COUNT]

    for i, img in enumerate(hits):
        img_url = img["largeImageURL"]
        img_data = requests.get(img_url).content
        with open(f"images/{i}.jpg", "wb") as f:
            f.write(img_data)

    print("✅ Face images downloaded")


# 🎬 VIDEO (REAL ANIMATION)
def create_video():
    inputs = []
    filters = []
    concat_inputs = ""

    for i in range(IMAGE_COUNT):
        inputs += ["-loop", "1", "-t", str(DURATION_PER_IMAGE), "-i", f"images/{i}.jpg"]
        filters.append(
            f"[{i}:v]scale=1280:720,zoompan=z='min(zoom+0.0008,1.2)':d=180[v{i}]"
        )
        concat_inputs += f"[v{i}]"

    filter_complex = ";".join(filters) + f";{concat_inputs}concat=n={IMAGE_COUNT}:v=1:a=0[outv]"

    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-i", "voice.m4a",
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-map", f"{IMAGE_COUNT}:a",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-shortest",
        "final.mp4"
    ]

    run(cmd)
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

    req = yt.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": "Unknown Facts About Humans",
                "description": "AI-generated animated facts video",
                "tags": ["facts", "unknown facts", "human psychology"],
                "categoryId": "27"
            },
            "status": {"privacyStatus": "public"}
        },
        media_body=MediaFileUpload("final.mp4", resumable=False)
    )

    res = req.execute()
    print("✅ Uploaded:", res["id"])


def main():
    print("🚀 Starting REAL animated face video pipeline")
    create_audio()
    download_images()
    create_video()
    upload()


if __name__ == "__main__":
    main()