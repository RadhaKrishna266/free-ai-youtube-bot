import os
import json
import subprocess
import requests
from pathlib import Path
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

# ================= CONFIG =================
TOPIC = "Mystery of Stonehenge"
CATEGORY = "History"

TARGET_MINUTES = 10
WORDS_PER_MIN = 140
TOTAL_IMAGES = 48

VOICE = "en-IN-PrabhatNeural"

IMAGE_DIR = "images"
VOICE_FILE = "voice.mp3"
VIDEO_FILE = "output.mp4"

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
# ========================================


def generate_script():
    base = f"""
Today we explore {TOPIC}, one of the greatest mysteries in {CATEGORY}.
This ancient site has fascinated historians, scientists, and archaeologists
for centuries.

Massive stones were moved with incredible precision using unknown techniques.
Some believe the site had astronomical importance, while others see religious meaning.

Despite modern technology, many secrets remain hidden.
Each discovery raises more questions than answers.

"""

    words_needed = TARGET_MINUTES * WORDS_PER_MIN
    script = ""

    while len(script.split()) < words_needed:
        script += base

    return script.strip()


def generate_voice(text):
    subprocess.run([
        "edge-tts",
        "--voice", VOICE,
        "--text", text,
        "--write-media", VOICE_FILE
    ], check=True)


def download_images():
    Path(IMAGE_DIR).mkdir(exist_ok=True)
    downloaded = 0

    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": TOPIC,
        "gsrlimit": TOTAL_IMAGES,
        "prop": "pageimages",
        "piprop": "original"
    }

    try:
        r = requests.get(url, params=params, timeout=10).json()
        pages = r.get("query", {}).get("pages", {})

        for i, page in enumerate(pages.values()):
            if "original" in page and downloaded < TOTAL_IMAGES:
                img_url = page["original"]["source"]
                img = requests.get(img_url, timeout=10).content
                with open(f"{IMAGE_DIR}/img_{i:03d}.jpg", "wb") as f:
                    f.write(img)
                downloaded += 1

    except Exception:
        downloaded = 0

    if downloaded < 10:
        for i in range(TOTAL_IMAGES):
            subprocess.run([
                "ffmpeg", "-y",
                "-f", "lavfi",
                "-i", "color=c=darkslategray:s=1280x720",
                "-frames:v", "1",
                f"{IMAGE_DIR}/img_{i:03d}.jpg"
            ], check=True)


def get_audio_duration():
    out = subprocess.check_output([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        VOICE_FILE
    ])
    return float(out.strip())


def create_animated_video():
    duration = get_audio_duration()
    img_duration = duration / TOTAL_IMAGES

    subprocess.run([
        "ffmpeg", "-y",
        "-framerate", f"1/{img_duration}",
        "-i", f"{IMAGE_DIR}/img_%03d.jpg",
        "-i", VOICE_FILE,
        "-vf",
        (
            "scale=1280:720,"
            "zoompan=z='min(zoom+0.0015,1.15)':"
            "x='iw/2-(iw/zoom/2)':"
            "y='ih/2-(ih/zoom/2)':"
            "d=125,"
            "fade=t=in:st=0:d=1,"
            "fade=t=out:st=4:d=1"
        ),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "slow",
        "-shortest",
        VIDEO_FILE
    ], check=True)


def load_credentials():
    raw = os.environ.get("YOUTUBE_CLIENT_SECRET")
    if not raw:
        raise RuntimeError("YOUTUBE_CLIENT_SECRET missing")

    info = json.loads(raw)
    return Credentials.from_authorized_user_info(info, SCOPES)


def upload_to_youtube():
    creds = load_credentials()
    youtube = build("youtube", "v3", credentials=creds)

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": TOPIC,
                "description": f"10 minute documentary on {TOPIC}.",
                "tags": ["history", "documentary", "ancient", "mystery"],
                "categoryId": "27"
            },
            "status": {
                "privacyStatus": "public"
            }
        },
        media_body=MediaFileUpload(VIDEO_FILE, resumable=True)
    )

    res = request.execute()
    print("✅ Uploaded:", res["id"])


def main():
    print("🚀 Starting 10+ min animated video pipeline")

    script = generate_script()
    generate_voice(script)

    download_images()
    create_animated_video()

    if not Path(VIDEO_FILE).exists():
        raise RuntimeError("Video not created")

    upload_to_youtube()


if __name__ == "__main__":
    main()