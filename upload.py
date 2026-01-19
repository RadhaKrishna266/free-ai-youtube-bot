import os
import json
import base64
import subprocess
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from PIL import Image

VIDEO_DURATION = 600  # 10 minutes


def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)


def create_audio():
    if os.path.exists("voice.mp3"):
        return
    print("🔊 Creating 10-minute audio")
    run([
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "anullsrc=r=44100:cl=stereo",
        "-t", str(VIDEO_DURATION),
        "voice.mp3"
    ])


def create_background():
    if os.path.exists("bg.jpg"):
        return
    print("🖼️ Creating background image")
    img = Image.new("RGB", (1280, 720), (15, 15, 15))
    img.save("bg.jpg")


def create_video():
    print("🎬 Creating animated video")
    run([
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", "bg.jpg",
        "-i", "voice.mp3",
        "-vf",
        "zoompan=z='min(zoom+0.0003,1.15)':d=25,scale=1280:720",
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        "-movflags", "+faststart",
        "final.mp4"
    ])


def get_authenticated_service():
    print("🔐 Authenticating YouTube")

    token_b64 = os.environ.get("YOUTUBE_TOKEN_BASE64")
    if not token_b64:
        raise RuntimeError("YOUTUBE_TOKEN_BASE64 secret missing")

    token_json = base64.b64decode(token_b64).decode()
    token_info = json.loads(token_json)

    creds = Credentials.from_authorized_user_info(
        token_info,
        scopes=["https://www.googleapis.com/auth/youtube.upload"]
    )

    return build("youtube", "v3", credentials=creds)


def upload_video():
    youtube = get_authenticated_service()

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": "The Mystery of Stonehenge",
                "description": "Auto-generated educational video",
                "tags": ["history", "stonehenge", "mystery"],
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
    create_audio()
    create_background()
    create_video()
    upload_video()


if __name__ == "__main__":
    main()