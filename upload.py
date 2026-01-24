import os
import json
import base64
import subprocess
import requests
import urllib.parse
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ================= CONFIG =================
PIXABAY_KEY = os.environ["PIXABAY_API_KEY"]

IMAGE_COUNT = 100          # 100 images × 6 sec = 10 minutes
IMAGE_DURATION = 6

SCRIPT_FILE = "script.txt"
VOICE_FILE = "narration.wav"

TANPURA_FILE = "audio/tanpura.mp3"
BELL_FILE = "audio/temple_bell.mp3"

FINAL_VIDEO = "final.mp4"
# ==========================================


def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)


# ================= AUDIO (HINDI PIPER) =================
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
    print("✅ Voice narration created")


# ================= IMAGES =================
def download_images():
    print("🖼️ Downloading temple images")

    os.makedirs("images", exist_ok=True)

    query = "kashi vishwanath temple shiva jyotirlinga varanasi"
    query = urllib.parse.quote(query)

    url = (
        f"https://pixabay.com/api/?key={PIXABAY_KEY}"
        f"&q={query}&image_type=photo&per_page=200"
    )

    data = requests.get(url, timeout=30).json()
    hits = data.get("hits", [])

    if len(hits) < IMAGE_COUNT:
        raise Exception("❌ Not enough temple images from Pixabay")

    for i in range(IMAGE_COUNT):
        img_url = hits[i]["largeImageURL"]
        img_data = requests.get(img_url, timeout=30).content
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
    print("🎬 Creating GOD DEVOTIONAL VIDEO")

    if not os.path.exists(TANPURA_FILE):
        raise Exception("❌ tanpura.mp3 missing in audio/")

    if not os.path.exists(BELL_FILE):
        raise Exception("❌ temple_bell.mp3 missing in audio/")

    run([
        "ffmpeg", "-y",

        "-f", "concat", "-safe", "0",
        "-i", "slideshow.txt",

        "-i", VOICE_FILE,
        "-stream_loop", "-1", "-i", TANPURA_FILE,
        "-stream_loop", "-1", "-i", BELL_FILE,

        "-filter_complex",
        (
            "[2:a]volume=0.25[a2];"
            "[3:a]volume=0.12[a3];"
            "[1:a][a2][a3]amix=inputs=3:normalize=0[a]"
        ),

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

    print("✅ Final devotional video created")


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
                "title": "काशी विश्वनाथ मंदिर का इतिहास | Shiva Temple Documentary",
                "description": (
                    "काशी विश्वनाथ मंदिर भगवान शिव के 12 ज्योतिर्लिंगों में से एक है।\n\n"
                    "🔔 मंदिर घंटी\n"
                    "🎵 तानपुरा भक्ति संगीत\n"
                    "🎤 हिंदी भक्ति वॉइस\n"
                    "🛕 AI Temple Documentary"
                ),
                "tags": ["kashi vishwanath", "shiva", "jyotirlinga", "temple history"],
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
    print("🔥 STARTING GOD ANIMATED VIDEO PIPELINE")
    create_audio()
    download_images()
    create_slideshow_file()
    create_video()
    upload()


if __name__ == "__main__":
    main()