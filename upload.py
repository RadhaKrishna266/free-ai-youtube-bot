import os
import json
import base64
import subprocess
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

DURATION = 600  # 10 minutes
IMAGE_TIME = 6  # seconds per image


def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)


# 🔊 CREATE AUDIBLE BACKGROUND SOUND
def create_audio():
    print("🔊 Creating audible background audio")
    run([
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "anoisesrc=color=pink:sample_rate=44100",
        "-t", str(DURATION),
        "-c:a", "aac",
        "-b:a", "192k",
        "audio.m4a"
    ])
    print("✅ audio created")


# 🎬 CREATE PHOTO SLIDESHOW WITH ZOOM ANIMATION
def create_video():
    print("🎬 Creating animated photo video")

    run([
        "ffmpeg", "-y",
        "-stream_loop", "-1",
        "-framerate", f"1/{IMAGE_TIME}",
        "-i", "images/%*.jpg",
        "-i", "audio.m4a",

        "-vf",
        f"zoompan=z='min(zoom+0.0008,1.08)':d={IMAGE_TIME*30}:s=1280x720,format=yuv420p",

        "-t", str(DURATION),
        "-r", "30",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-c:a", "aac",
        "-shortest",
        "final.mp4"
    ])

    print("✅ final.mp4 created (PHOTOS + MOTION + AUDIO)")


# 🔐 AUTH
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
                "description": "Animated history video with visuals and sound",
                "tags": ["Stonehenge", "History", "Mystery"],
                "categoryId": "27"
            },
            "status": {
                "privacyStatus": "public",
                "selfDeclaredMadeForKids": False
            }
        },
        media_body=MediaFileUpload("final.mp4", resumable=True)
    )

    response = request.execute()
    print("✅ Uploaded:", response["id"])


def main():
    print("🚀 Starting REAL photo animation pipeline")

    create_audio()
    create_video()
    upload_video()


if __name__ == "__main__":
    main()