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

IMAGE_COUNT = 100          # 100 × 6 sec = 10 min
IMAGE_DURATION = 6

SCRIPT_FILE = "script.txt"
VOICE_FILE = "narration.wav"

TANPURA_FILE = "audio/tanpura.mp3"
BELL_FILE = "audio/temple_bell.mp3"

FINAL_VIDEO = "final.mp4"

# 🔥 MUST MATCH YAML
PIPER_BIN = "./piper/piper"
PIPER_MODEL = "piper/hi_IN-cmu_indic-medium.onnx"
# ==========================================

def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)

# ================= AUDIO =================
def create_audio():
    print("🎤 Creating Hindi devotional narration")

    if not os.path.exists(PIPER_MODEL):
        raise RuntimeError("❌ Hindi Piper model missing")

    if not os.path.exists(SCRIPT_FILE):
        raise RuntimeError("❌ script.txt missing")

    with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
        text = f.read()

    subprocess.run(
        [PIPER_BIN, "--model", PIPER_MODEL, "--output_file", VOICE_FILE],
        input=text.encode("utf-8"),
        check=True
    )

    print("✅ Hindi narration created")

# ================= IMAGES =================
def download_images():
    print("🖼️ Downloading temple images")
    os.makedirs("images", exist_ok=True)

    query = "kashi vishwanath temple shiva varanasi"
    url = (
        f"https://pixabay.com/api/?key={PIXABAY_KEY}"
        f"&q={query}&image_type=photo&per_page=200"
    )

    hits = requests.get(url).json().get("hits", [])

    if len(hits) < IMAGE_COUNT:
        raise RuntimeError("❌ Not enough temple images")

    for i in range(IMAGE_COUNT):
        img_data = requests.get(hits[i]["largeImageURL"]).content
        with open(f"images/{i:03}.jpg", "wb") as f:
            f.write(img_data)

    print("✅ Images downloaded")

# ================= SLIDESHOW =================
def create_slideshow():
    with open("slideshow.txt", "w") as f:
        for img in sorted(os.listdir("images")):
            f.write(f"file 'images/{img}'\n")
            f.write(f"duration {IMAGE_DURATION}\n")

# ================= VIDEO =================
def create_video():
    print("🎬 Creating devotional video")

    if not os.path.exists(TANPURA_FILE) or not os.path.exists(BELL_FILE):
        raise RuntimeError("❌ Tanpura or Bell audio missing")

    run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", "slideshow.txt",

        "-i", VOICE_FILE,
        "-stream_loop", "-1", "-i", TANPURA_FILE,
        "-stream_loop", "-1", "-i", BELL_FILE,

        "-filter_complex",
        "[2:a]volume=0.25[a2];"
        "[3:a]volume=0.15[a3];"
        "[1:a][a2][a3]amix=inputs=3:dropout_transition=3[a]",

        "-map", "0:v",
        "-map", "[a]",

        "-vf",
        "scale=1280:720:force_original_aspect_ratio=decrease,"
        "pad=1280:720:(ow-iw)/2:(oh-ih)/2",

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
    yt = youtube_service()

    req = yt.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": "काशी विश्वनाथ मंदिर का रहस्य | Shiva Temple History",
                "description": "काशी विश्वनाथ ज्योतिर्लिंग का दिव्य इतिहास | Shiv Bhakti | Temple Series",
                "tags": ["kashi", "shiv bhakti", "jyotirlinga", "temple history"],
                "categoryId": "27"
            },
            "status": {"privacyStatus": "public"}
        },
        media_body=MediaFileUpload(FINAL_VIDEO, resumable=False)
    )

    print("✅ Uploaded:", req.execute()["id"])

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