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


# 🔊 CREATE CLEAR AUDIBLE AUDIO
def create_audio():
    print("🔊 Creating audible audio (10 min)")
    run([
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "sine=frequency=440:sample_rate=44100",
        "-t", str(DURATION),
        "-filter:a", "volume=0.4",
        "-c:a", "mp3",
        "voice.mp3"
    ])
    print("✅ voice.mp3 created")


# 🎬 CREATE REAL ANIMATED VIDEO (NOT TEST BARS)
def create_animated_video():
    print("🎬 Creating REAL animated video")

    run([
        "ffmpeg", "-y",

        # 🌈 animated gradient background (REAL animation)
        "-f", "lavfi",
        "-i", f"gradients=size=1280x720:duration={DURATION}:speed=0.03",

        # 🔊 audio
        "-i", "voice.mp3",

        # 🎥 encoding
        "-map", "0:v",
        "-map", "1:a",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-pix_fmt", "yuv420p",
        "-r", "30",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        "final.mp4"
    ])

    print("✅ final.mp4 created (ANIMATED + AUDIO)")


# 🔐 AUTHENTICATION
def get_authenticated_service():
    print("🔐 Authenticating YouTube")

    token = base64.b64decode(
        os.environ["YOUTUBE_TOKEN_BASE64"]
    ).decode("utf-8")

    creds = Credentials.from_authorized_user_info(
        json.loads(token),
        ["https://www.googleapis.com/auth/youtube.upload"]
    )

    return build("youtube", "v3", credentials=creds)


# 🚀 UPLOAD VIDEO
def upload_video():
    youtube = get_authenticated_service()

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": "The Mystery of Stonehenge",
                "description": "Fully animated AI-generated video with audio",
                "tags": ["Stonehenge", "History", "Mystery", "AI Video"],
                "categoryId": "27"
            },
            "status": {
                "privacyStatus": "public",
                "selfDeclaredMadeForKids": False
            }
        },
        media_body=MediaFileUpload(
            "final.mp4",
            chunksize=-1,
            resumable=True
        )
    )

    response = request.execute()
    print("✅ Uploaded video ID:", response["id"])


def main():
    print("🚀 Starting FULL animated pipeline")

    create_audio()
    create_animated_video()

    # ⚠️ Upload may fail if daily limit exceeded
    upload_video()


if __name__ == "__main__":
    main()