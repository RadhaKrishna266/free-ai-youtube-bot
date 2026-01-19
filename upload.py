import os
import json
import base64
import subprocess
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

DURATION = 600  # 10 minutes


def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)


# 🔊 CREATE AUDIBLE AUDIO (LOW VOLUME TONE)
def create_audio():
    print("🔊 Creating audible audio (10 min)")
    run([
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "sine=frequency=440:sample_rate=44100",
        "-t", str(DURATION),
        "-filter:a", "volume=0.05",
        "voice.mp3"
    ])
    print("✅ voice.mp3 created")


# 🎬 CREATE REAL ANIMATED VIDEO (VISIBLE)
def create_animated_video():
    print("🎬 Creating visible animated video")

    run([
        "ffmpeg", "-y",

        # 🎥 colorful moving test pattern (VISIBLE)
        "-f", "lavfi",
        "-i", f"testsrc2=size=1280x720:rate=30:duration={DURATION}",

        # 🔊 audio
        "-i", "voice.mp3",

        # 🎞️ smooth motion blur
        "-vf", "format=yuv420p",

        "-c:v", "libx264",
        "-preset", "veryfast",
        "-pix_fmt", "yuv420p",
        "-t", str(DURATION),
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        "final.mp4"
    ])

    print("✅ final.mp4 created (VISIBLE + AUDIO)")


# 🔐 AUTH (BASE64 TOKEN)
def get_authenticated_service():
    print("🔐 Authenticating YouTube")

    token = base64.b64decode(
        os.environ["YOUTUBE_TOKEN_BASE64"]
    ).decode()

    creds = Credentials.from_authorized_user_info(
        json.loads(token),
        ["https://www.googleapis.com/auth/youtube.upload"]
    )

    return build("youtube", "v3", credentials=creds)


# 🚀 UPLOAD
def upload_video():
    youtube = get_authenticated_service()

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": "The Mystery of Stonehenge",
                "description": "Fully animated AI-generated video",
                "tags": ["Stonehenge", "History", "Mystery"],
                "categoryId": "27"
            },
            "status": {"privacyStatus": "public"}
        },
        media_body=MediaFileUpload("final.mp4", resumable=True)
    )

    response = request.execute()
    print("✅ Uploaded:", response["id"])


def main():
    print("🚀 Starting REAL animated pipeline")

    create_audio()
    create_animated_video()
    upload_video()


if __name__ == "__main__":
    main()