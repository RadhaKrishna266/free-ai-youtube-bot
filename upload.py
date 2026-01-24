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

SCRIPT_FILE = "script.txt"
VOICE_FILE = "narration.wav"
FINAL_VIDEO = "final.mp4"
SLIDESHOW_FILE = "slideshow.txt"

IMAGE_COUNT = 100        # 100 images × 6 sec = 10 minutes
IMAGE_DURATION = 6

SEARCH_QUERY = "ancient indian temple god hindu"  # CHANGE PER VIDEO

# =========================================

def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)

# ================= AUDIO (HINDI GOD VOICE) =================
def create_audio():
    print("🎤 Creating Hindi devotional narration")

    if not os.path.exists(SCRIPT_FILE):
        raise Exception("❌ script.txt missing")

    with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
        text = f.read()

    cmd = [
        "./piper/piper",
        "--model", "piper/hi_IN-cmu_indic-medium.onnx",
        "--output_file", VOICE_FILE
    ]

    subprocess.run(cmd, input=text.encode("utf-8"), check=True)
    print("✅ Narration created")

# ================= IMAGES (TEMPLES / GOD) =================
def download_images():
    print("🖼️ Downloading temple images")
    os.makedirs("images", exist_ok=True)

    url = (
        f"https://pixabay.com/api/?key={PIXABAY_KEY}"
        f"&q={SEARCH_QUERY.replace(' ', '+')}"
        "&image_type=photo&orientation=horizontal&per_page=200"
    )

    data = requests.get(url, timeout=30).json()
    hits = data.get("hits", [])

    if len(hits) < IMAGE_COUNT:
        raise Exception("❌ Not enough images from Pixabay")

    for i in range(IMAGE_COUNT):
        img_url = hits[i]["largeImageURL"]
        img_data = requests.get(img_url, timeout=30).content
        with open(f"images/{i:03}.jpg", "wb") as f:
            f.write(img_data)

    print(f"✅ {IMAGE_COUNT} images downloaded")

# ================= SLIDESHOW =================
def create_slideshow():
    print("📝 Creating slideshow file")

    with open(SLIDESHOW_FILE, "w") as f:
        for img in sorted(os.listdir("images")):
            f.write(f"file 'images/{img}'\n")
            f.write(f"duration {IMAGE_DURATION}\n")

# ================= VIDEO (DIVINE ANIMATION) =================
def create_video():
    print("🎬 Creating God-style animated video")

    run([
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", SLIDESHOW_FILE,
        "-i", VOICE_FILE,
        "-i", "assets/tanpura.mp3",
        "-i", "assets/bell.mp3",
        "-filter_complex",
        (
            "[0:v]scale=1280:720:force_original_aspect_ratio=decrease,"
            "pad=1280:720:(ow-iw)/2:(oh-ih)/2,"
            "zoompan=z='min(zoom+0.0004,1.12)':d=150,"
            "colorbalance=rs=0.06:gs=0.05:bs=-0.03[v];"
            "[2:a]volume=0.25[bg];"
            "[3:a]adelay=1000|1000,volume=0.4[bell];"
            "[1:a][bg][bell]amix=inputs=3:dropout_transition=2[a]"
        ),
        "-map", "[v]",
        "-map", "[a]",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-shortest",
        FINAL_VIDEO
    ])

    print("✅ Final video created")

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
    print("🚀 Uploading video to YouTube")

    yt = youtube_service()

    request = yt.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": "Divine Indian Temple History | God Documentary",
                "description": "A calm devotional journey through ancient Indian temples with Hindi narration.",
                "tags": ["god", "temple", "hindu", "bhakti", "indian history"],
                "categoryId": "27"
            },
            "status": {"privacyStatus": "public"}
        },
        media_body=MediaFileUpload(FINAL_VIDEO, resumable=False)
    )

    res = request.execute()
    print("✅ Uploaded video ID:", res["id"])

# ================= MAIN =================
def main():
    print("🔥 STARTING GOD ANIMATED VIDEO PIPELINE")
    create_audio()
    download_images()
    create_slideshow()
    create_video()
    upload()

if __name__ == "__main__":
    main()