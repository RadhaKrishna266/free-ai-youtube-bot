import os
import json
import subprocess
import requests
from glob import glob
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ---------------- CONFIG ----------------
TITLE = "The Mystery of Stonehenge"
DESCRIPTION = "A fully animated documentary exploring the mystery of Stonehenge."
TAGS = ["stonehenge", "history", "documentary", "ancient"]
VOICE = "en-US-GuyNeural"
QUERY = "Stonehenge"
FPS = 30
IMG_DURATION = 8  # seconds per image
TARGET_MINUTES = 10
# ---------------------------------------


def run(cmd):
    subprocess.run(cmd, check=True)


def generate_script():
    base = (
        "Stonehenge is one of the most mysterious ancient monuments in the world. "
        "Built over four thousand years ago, its massive stones were transported "
        "from distant regions using unknown techniques. Scholars believe it may "
        "have been used for astronomical observations, sacred rituals, or burial "
        "ceremonies. Despite modern technology, its true purpose remains debated. "
    )
    return base * 40  # ~10 minutes narration


def generate_voice(text):
    print("🔊 Generating voice narration...")
    run([
        "edge-tts",
        "--voice", VOICE,
        "--text", text,
        "--write-media", "voice.mp3"
    ])


def download_images():
    print("🖼️ Downloading images from Wikipedia...")
    os.makedirs("images", exist_ok=True)

    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": QUERY,
        "gsrlimit": 25,
        "prop": "pageimages",
        "piprop": "original",
        "format": "json"
    }

    r = requests.get(url, params=params, timeout=20)
    data = r.json()

    pages = data.get("query", {}).get("pages", {})
    count = 0

    for page in pages.values():
        if "original" in page:
            img_url = page["original"]["source"]
            img_data = requests.get(img_url, timeout=20).content
            with open(f"images/img_{count:02d}.jpg", "wb") as f:
                f.write(img_data)
            count += 1

    if count < 5:
        print("⚠️ Not enough images — generating fallback images")
        create_fallback_images()


def create_fallback_images():
    for i in range(20):
        run([
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", "color=c=darkslategray:s=1280x720",
            "-frames:v", "1",
            f"images/img_{i:02d}.jpg"
        ])


def create_video():
    print("🎞️ Creating animated video...")
    os.makedirs("clips", exist_ok=True)

    images = sorted(glob("images/*.jpg"))
    if not images:
        raise RuntimeError("No images available")

    clips = []

    for i, img in enumerate(images):
        clip = f"clips/c_{i}.mp4"
        clips.append(clip)

        run([
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", img,
            "-vf",
            "zoompan=z='min(zoom+0.001,1.2)':"
            "x='iw/2-(iw/zoom/2)':"
            "y='ih/2-(ih/zoom/2)':"
            f"d={IMG_DURATION*FPS}:s=1280x720",
            "-t", str(IMG_DURATION),
            "-r", str(FPS),
            "-pix_fmt", "yuv420p",
            clip
        ])

    with open("clips/list.txt", "w") as f:
        for c in clips:
            f.write(f"file '{c}'\n")

    run([
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", "clips/list.txt",
        "-i", "voice.mp3",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-shortest",
        "-pix_fmt", "yuv420p",
        "final.mp4"
    ])


def load_credentials():
    raw = os.getenv("YOUTUBE_TOKEN_JSON")
    if not raw:
        print("⚠️ No YouTube token — skipping upload")
        return None

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        print("⚠️ Invalid token JSON — skipping upload")
        return None

    return Credentials.from_authorized_user_info(
        data, ["https://www.googleapis.com/auth/youtube.upload"]
    )


def upload_video():
    creds = load_credentials()
    if not creds:
        return

    print("🚀 Uploading to YouTube...")
    yt = build("youtube", "v3", credentials=creds)

    req = yt.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": TITLE,
                "description": DESCRIPTION,
                "tags": TAGS,
                "categoryId": "27"
            },
            "status": {"privacyStatus": "public"}
        },
        media_body=MediaFileUpload("final.mp4", resumable=True)
    )

    res = req.execute()
    print("✅ Uploaded video ID:", res["id"])


def main():
    print("🚀 Starting full animated video pipeline")
    script = generate_script()
    generate_voice(script)
    download_images()
    create_video()
    upload_video()


if __name__ == "__main__":
    main()