import os
import subprocess
import textwrap
import json
import math
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

# ================== CONFIG ==================
TOPIC = "Mystery of Stonehenge"
VIDEO_FILE = "final.mp4"
SCRIPT_FILE = "script.txt"
VOICE_FILE = "voice.mp3"
IMAGE_DIR = "images"
FPS = 25
IMAGE_DURATION = 6  # seconds per image
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
# ============================================


def generate_script():
    print("📝 Generating long script...")
    script = f"""
    {TOPIC}

    Introduction explaining history and mystery.

    Origins and theories with detailed explanations.

    Archaeological discoveries.

    Cultural and astronomical significance.

    Modern research and unanswered questions.

    Conclusion summarizing importance.
    """
    script = "\n\n".join([script] * 8)  # makes ~6–8 min
    with open(SCRIPT_FILE, "w") as f:
        f.write(textwrap.dedent(script))


def generate_voice():
    print("🔊 Generating voice...")
    subprocess.run([
        "edge-tts",
        "--voice", "en-IN-PrabhatNeural",
        "--rate", "+0%",
        "--file", SCRIPT_FILE,
        "--write-media", VOICE_FILE
    ], check=True)


def download_images():
    print("🖼️ Downloading images...")
    os.makedirs(IMAGE_DIR, exist_ok=True)
    for i in range(1, 61):
        subprocess.run([
            "curl",
            "-L",
            f"https://source.unsplash.com/1920x1080/?{TOPIC.replace(' ', ',')}",
            "-o",
            f"{IMAGE_DIR}/{i}.jpg"
        ])


def get_audio_duration():
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration", "-of",
         "default=noprint_wrappers=1:nokey=1", VOICE_FILE],
        stdout=subprocess.PIPE
    )
    return float(result.stdout)


def create_video():
    print("🎬 Creating video...")
    duration = math.ceil(get_audio_duration())
    image_count = math.ceil(duration / IMAGE_DURATION)

    with open("images.txt", "w") as f:
        for i in range(1, image_count + 1):
            f.write(f"file '{IMAGE_DIR}/{(i % 60) + 1}.jpg'\n")
            f.write(f"duration {IMAGE_DURATION}\n")

    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", "images.txt",
        "-vf", "scale=1920:1080",
        "-r", str(FPS),
        "-pix_fmt", "yuv420p",
        "video.mp4"
    ], check=True)

    subprocess.run([
        "ffmpeg", "-y",
        "-i", "video.mp4",
        "-i", VOICE_FILE,
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        VIDEO_FILE
    ], check=True)


def get_authenticated_service():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            "client_secret.json", SCOPES)
        creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return build("youtube", "v3", credentials=creds)


def upload_to_youtube():
    print("🚀 Uploading to YouTube...")
    youtube = get_authenticated_service()

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": TOPIC,
                "description": f"Full documentary on {TOPIC}",
                "tags": [TOPIC, "history", "mystery"],
                "categoryId": "27"
            },
            "status": {
                "privacyStatus": "public"
            }
        },
        media_body=MediaFileUpload(VIDEO_FILE, chunksize=-1, resumable=True)
    )

    response = request.execute()
    print("✅ Uploaded:", response["id"])


def main():
    print("🚀 Starting full pipeline")
    generate_script()
    generate_voice()
    download_images()
    create_video()
    upload_to_youtube()


if __name__ == "__main__":
    main()