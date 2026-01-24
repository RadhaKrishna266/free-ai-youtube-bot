import os
import json
import base64
import subprocess
import requests
from gtts import gTTS
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ============== CONFIG =================
PIXABAY_KEY = os.environ["PIXABAY_API_KEY"]

IMAGE_COUNT = 100          # 100 images × 6 sec = 10 minutes
IMAGE_DURATION = 6

SCRIPT_FILE = "script.txt"
VOICE_FILE = "narration.mp3"

TANPURA_FILE = "audio/tanpura.mp3"
BELL_FILE = "audio/temple_bell.mp3"

FINAL_VIDEO = "final.mp4"
# =======================================

def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)

# ============== HINDI VOICE ==============
def create_audio():
    print("🎤 Creating REAL Hindi narration (Google TTS)")

    with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
        text = f.read()

    tts = gTTS(text=text, lang="hi", slow=False)
    tts.save(VOICE_FILE)

    print("✅ Hindi narration ready")

# ============== IMAGES ===================
def download_images():
    print("🖼️ Downloading temple images")
    os.makedirs("images", exist_ok=True)

    query = "kashi vishwanath temple shiva jyotirlinga varanasi ghat"
    url = (
        f"https://pixabay.com/api/?key={PIXABAY_KEY}"
        f"&q={query}&image_type=photo&per_page=200"
    )

    hits = requests.get(url).json()["hits"]

    for i in range(IMAGE_COUNT):
        img = hits[i]["largeImageURL"]
        data = requests.get(img).content
        with open(f"images/{i:03}.jpg", "wb") as f:
            f.write(data)

    print("✅ Images downloaded")

# ============== SLIDESHOW =================
def create_slideshow():
    with open("slideshow.txt", "w") as f:
        for img in sorted(os.listdir("images")):
            f.write(f"file 'images/{img}'\n")
            f.write(f"duration {IMAGE_DURATION}\n")

# ============== VIDEO =====================
def create_video():
    print("🎬 Creating GOD STYLE VIDEO")

    run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", "slideshow.txt",
        "-i", VOICE_FILE,
        "-stream_loop", "-1", "-i", TANPURA_FILE,
        "-stream_loop", "-1", "-i", BELL_FILE,
        "-filter_complex",
        "[2:a]volume=0.25[a2];"
        "[3:a]volume=0.12[a3];"
        "[1:a][a2][a3]amix=inputs=3[a]",
        "-map", "0:v",
        "-map", "[a]",
        "-vf",
        "scale=1280:720:force_original_aspect_ratio=decrease,"
        "pad=1280:720:(ow-iw)/2:(oh-ih)/2,"
        "zoompan=z='min(zoom+0.0005,1.1)':d=125",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-shortest",
        FINAL_VIDEO
    ])

    print("✅ Final video created")

# ============== YOUTUBE ===================
def upload():
    token = json.loads(
        base64.b64decode(os.environ["YOUTUBE_TOKEN_BASE64"]).decode()
    )

    creds = Credentials.from_authorized_user_info(
        token,
        ["https://www.googleapis.com/auth/youtube.upload"]
    )

    yt = build("youtube", "v3", credentials=creds)

    yt.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": "काशी विश्वनाथ मंदिर का रहस्य | Temple Series Ep 1",
                "description": "काशी विश्वनाथ मंदिर का इतिहास, रहस्य और शिव भक्ति",
                "tags": ["kashi", "shiv", "temple history", "bhakti"],
                "categoryId": "27"
            },
            "status": {"privacyStatus": "public"}
        },
        media_body=MediaFileUpload(FINAL_VIDEO)
    ).execute()

    print("🚀 Uploaded to YouTube")

# ============== MAIN ======================
def main():
    create_audio()
    download_images()
    create_slideshow()
    create_video()
    upload()

if __name__ == "__main__":
    main()