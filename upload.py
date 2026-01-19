import os
import json
import subprocess
import sys
from glob import glob
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ---------------- CONFIG ----------------
TITLE = "The Mystery of Stonehenge"
DESCRIPTION = "An animated documentary exploring the mystery of Stonehenge."
TAGS = ["stonehenge", "history", "mystery", "documentary"]
VOICE = "en-US-GuyNeural"
IMAGE_QUERY = "Stonehenge ancient monument"
DURATION_PER_IMAGE = 6  # seconds
FPS = 30
# ---------------------------------------


def run(cmd):
    subprocess.run(cmd, check=True)


def generate_script():
    return (
        "Stonehenge is one of the most mysterious ancient structures on Earth. "
        "Built over four thousand years ago, its massive stones were transported "
        "from great distances. Scholars believe it was used for astronomy, rituals, "
        "or spiritual ceremonies. Despite decades of research, its true purpose "
        "remains unknown, making Stonehenge a timeless mystery."
    ) * 8  # repeat to reach ~10 minutes


def generate_voice(script):
    print("🔊 Generating voice narration...")
    run([
        "edge-tts",
        "--voice", VOICE,
        "--text", script,
        "--write-media", "voice.mp3"
    ])


def download_images():
    print("🖼️ Downloading images...")
    os.makedirs("images", exist_ok=True)

    run([
        "python", "-m", "bing_image_downloader",
        IMAGE_QUERY,
        "--limit", "20",
        "--output_dir", "images",
        "--adult_filter_off",
        "--force_replace",
        "--timeout", "60"
    ])


def create_animated_video():
    print("🎞️ Creating animated video...")
    os.makedirs("clips", exist_ok=True)

    images = glob("images/*/*.jpg")
    if not images:
        raise RuntimeError("No images found")

    clips = []

    for i, img in enumerate(images):
        clip = f"clips/clip_{i}.mp4"
        clips.append(clip)

        run([
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", img,
            "-vf",
            "zoompan=z='min(zoom+0.0008,1.15)':"
            "x='iw/2-(iw/zoom/2)':"
            "y='ih/2-(ih/zoom/2)':"
            f"d={DURATION_PER_IMAGE * FPS}:s=1280x720",
            "-t", str(DURATION_PER_IMAGE),
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
        raise RuntimeError("YOUTUBE_TOKEN_JSON missing")

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        raise RuntimeError("Invalid YOUTUBE_TOKEN_JSON")

    return Credentials.from_authorized_user_info(data, ["https://www.googleapis.com/auth/youtube.upload"])


def upload_to_youtube():
    print("🚀 Uploading to YouTube...")
    creds = load_credentials()
    youtube = build("youtube", "v3", credentials=creds)

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": TITLE,
                "description": DESCRIPTION,
                "tags": TAGS,
                "categoryId": "27"
            },
            "status": {
                "privacyStatus": "public"
            }
        },
        media_body=MediaFileUpload("final.mp4", resumable=True)
    )

    response = request.execute()
    print("✅ Uploaded:", response["id"])


def main():
    print("🚀 Starting full animated video pipeline")

    script = generate_script()
    generate_voice(script)
    download_images()
    create_animated_video()

    if os.getenv("YOUTUBE_TOKEN_JSON"):
        upload_to_youtube()
    else:
        print("⚠️ No YouTube credentials — skipping upload")


if __name__ == "__main__":
    main()