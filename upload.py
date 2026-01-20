import os
import json
import base64
import subprocess
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

DURATION = 600  # 10 minutes
FPS = 30


def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)


# 🔊 CREATE REAL AUDIBLE AUDIO (YOUTUBE SAFE)
def create_audio():
    print("🔊 Creating audio")
    run([
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "anoisesrc=color=brown:sample_rate=44100",
        "-t", str(DURATION),
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "44100",
        "audio.aac"
    ])
    print("✅ audio.aac created")


# 🎬 CREATE GUARANTEED-PROCESSABLE VIDEO
def create_video():
    print("🎬 Creating YouTube-safe animated video")

    run([
        "ffmpeg", "-y",

        # ✅ guaranteed visible animation
        "-f", "lavfi",
        "-i", f"testsrc2=size=1280x720:rate={FPS}:duration={DURATION}",

        "-i", "audio.aac",

        "-map", "0:v:0",
        "-map", "1:a:0",

        "-c:v", "libx264",
        "-profile:v", "high",
        "-level", "4.2",
        "-pix_fmt", "yuv420p",
        "-r", str(FPS),
        "-g", str(FPS * 2),
        "-preset", "slow",
        "-movflags", "+faststart",

        "-c:a", "aac",
        "-b:a", "192k",

        "-shortest",
        "final.mp4"
    ])

    print("✅ final.mp4 created (YouTube SAFE)")


# 🔐 AUTH USING BASE64 TOKEN
def get_authenticated_service():
    token = base64.b64decode(
        os.environ["YOUTUBE_TOKEN_BASE64"]
    ).decode("utf-8")

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
                "description": "Animated educational video",
                "tags": ["Stonehenge", "History", "Mystery"],
                "categoryId": "27"
            },
            "status": {
                "privacyStatus": "public",
                "selfDeclaredMadeForKids": False
            }
        },
        media_body=MediaFileUpload(
            "final.mp4",
            mimetype="video/mp4",
            resumable=True
        )
    )

    response = request.execute()
    print("✅ Uploaded:", response["id"])


def main():
    print("🚀 Starting FINAL stable pipeline")
    create_audio()
    create_video()
    upload_video()


if __name__ == "__main__":
    main()