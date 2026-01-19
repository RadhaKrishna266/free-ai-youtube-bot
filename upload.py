import os
import subprocess
import textwrap
import json
import requests
from pathlib import Path

# ================= CONFIG =================
TOPIC = "Mystery of Stonehenge"
TARGET_MINUTES = 7            # change 5–10
VOICE = "en-IN-PrabhatNeural"
FPS = 25
RESOLUTION = "1920x1080"
IMAGE_DURATION = 6            # seconds per image
MIN_IMAGES = 60
# =========================================


def generate_long_script(topic, minutes):
    words = minutes * 140
    paragraph = f"""
    Today we explore {topic}. This ancient monument has fascinated historians,
    archaeologists, and scientists for centuries. Located in England, Stonehenge
    raises questions about human intelligence, astronomy, and forgotten civilizations.
    """
    script = (" ".join([paragraph] * 20))[:words * 6]
    return textwrap.fill(script, 90)


def generate_voice(script):
    Path("chunks").mkdir(exist_ok=True)
    words = script.split()
    chunk_size = 400
    audio_files = []

    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i + chunk_size])
        txt = f"chunks/{i}.txt"
        mp3 = f"chunks/{i}.mp3"

        with open(txt, "w") as f:
            f.write(chunk)

        subprocess.run([
            "edge-tts",
            "--voice", VOICE,
            "--file", txt,
            "--write-media", mp3
        ], check=True)

        audio_files.append(mp3)

    with open("audio_list.txt", "w") as f:
        for a in audio_files:
            f.write(f"file '{a}'\n")

    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", "audio_list.txt", "-c", "copy", "voice.mp3"
    ], check=True)


def download_images(topic):
    Path("images").mkdir(exist_ok=True)
    images = []

    for i in range(MIN_IMAGES):
        url = f"https://picsum.photos/1920/1080?random={i}"
        img = f"images/{i}.jpg"
        r = requests.get(url, timeout=10)
        with open(img, "wb") as f:
            f.write(r.content)
        images.append(img)

    return images


def build_video(images):
    with open("images.txt", "w") as f:
        for img in images:
            f.write(f"file '{img}'\n")
            f.write(f"duration {IMAGE_DURATION}\n")

    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", "images.txt",
        "-vf", f"scale={RESOLUTION}",
        "-r", str(FPS),
        "-pix_fmt", "yuv420p",
        "video.mp4"
    ], check=True)


def merge_audio_video():
    subprocess.run([
        "ffmpeg", "-y",
        "-i", "video.mp4",
        "-i", "voice.mp3",
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        "final.mp4"
    ], check=True)


# ============ YOUTUBE (OPTIONAL) ============
def upload_to_youtube():
    if "YOUTUBE_CLIENT_SECRET" not in os.environ:
        print("⚠️ YouTube secrets missing → skipping upload")
        return

    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from google.oauth2.credentials import Credentials

    creds = Credentials.from_authorized_user_info(
        json.loads(os.environ["YOUTUBE_CLIENT_SECRET"]),
        ["https://www.googleapis.com/auth/youtube.upload"]
    )

    youtube = build("youtube", "v3", credentials=creds)

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": TOPIC,
                "description": f"Complete documentary about {TOPIC}",
                "tags": ["history", "mystery", "documentary"],
                "categoryId": "22"
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
    print("🚀 Starting auto video pipeline")
    print("Topic:", TOPIC)

    script = generate_long_script(TOPIC, TARGET_MINUTES)
    generate_voice(script)

    images = download_images(TOPIC)
    build_video(images)

    merge_audio_video()
    print("✅ final.mp4 created")

    upload_to_youtube()


if __name__ == "__main__":
    main()