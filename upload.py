import os
import json
import base64
import subprocess
import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ================= CONFIG =================
PIXABAY_KEY = os.environ["PIXABAY_API_KEY"]
IMAGE_COUNT = 100          # 100 images × 6 sec = 10 minutes
IMAGE_DURATION = 6
SCRIPT_FILE = "script.txt"
VOICE_FILE = "narration.wav"
FINAL_VIDEO = "final.mp4"

# ==========================================

def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)

# ================= AUDIO (REAL VOICE) =================
def create_audio():
    print("🎤 Creating narration using Piper")

    if not os.path.exists(SCRIPT_FILE):
        raise Exception("❌ script.txt missing (must be long text)")

    with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
        text = f.read()

    cmd = [
        "./piper/piper",
        "--model", "piper/en_US-lessac-medium.onnx",
        "--output_file", VOICE_FILE
    ]

    subprocess.run(cmd, input=text.encode(), check=True)
    print("✅ Audio created")

# ================= IMAGES =================
def download_images():
    print("🖼️ Downloading images")
    os.makedirs("images", exist_ok=True)

    url = (
        f"https://pixabay.com/api/?key={PIXABAY_KEY}"
        "&q=india+history+people"
        "&image_type=photo&per_page=200"
    )

    data = requests.get(url).json()
    hits = data.get("hits", [])

    if len(hits) < IMAGE_COUNT:
        raise Exception("❌ Not enough images from Pixabay")

    for i in range(IMAGE_COUNT):
        img_url = hits[i]["largeImageURL"]
        img_data = requests.get(img_url).content
        with open(f"images/{i:03}.jpg", "wb") as f:
            f.write(img_data)

    print(f"✅ {IMAGE_COUNT} images downloaded")

# ================= SLIDESHOW =================
def create_slideshow_file():
    print("📝 Creating slideshow list")
    with open("slideshow.txt", "w") as f:
        for img in sorted(os.listdir("images")):
            f.write(f"file 'images/{img}'\n")
            f.write(f"duration {IMAGE_DURATION}\n")

# ================= VIDEO =================
def create_video():
    print("🎬 Creating final video")

    run([
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", "slideshow.txt",
        "-i", VOICE_FILE,
        "-vf",
        (
            "scale=1280:720:force_original_aspect_ratio=decrease,"
            "pad=1280:720:(ow-iw)/2:(oh-ih)/2"
        ),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-shortest",
        FINAL_VIDEO
    ])

    print("✅ Video created")

# ================= YOUTUBE =================
def youtube_service():
    token = json.loads(
        base64.b64decode(os.environ["YOUTUBE_TOKEN_BASE64"]).decode()
    )

    creds = Credentials.from_authorized_user_info(
        token,
        ["https://www.googleapis.com/auth/youtube.upload"]
    )

    return build("youtube", "v3", credentials=creds)

def upload():
    print("🚀 Uploading to YouTube")

    yt = youtube_service()

    request = yt.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": "Ancient Indian History Facts | AI Documentary",
                "description": "10 minute AI generated history video with narration and images",
                "tags": ["history", "india", "facts", "ai documentary"],
                "categoryId": "27"
            },
            "status": {"privacyStatus": "public"}
        },
        media_body=MediaFileUpload(FINAL_VIDEO, resumable=False)
    )

    res = request.execute()
    print("✅ Uploaded:", res["id"])

# ================= MAIN =================
def main():
    print("🔥 Starting FULL AI VIDEO PIPELINE")
    create_audio()
    download_images()
    create_slideshow_file()
    create_video()
    upload()

if __name__ == "__main__":
    main()