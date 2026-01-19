import os
import json
import base64
import subprocess
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

VIDEO_DURATION = 600  # 10 minutes
FPS = 25


def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)


# 🔊 CREATE SILENT AUDIO (10 MIN)
def create_audio():
    print("🔊 Creating silent voice.mp3 (10 minutes)")
    run([
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "anullsrc=r=44100:cl=stereo",
        "-t", str(VIDEO_DURATION),
        "-c:a", "mp3",
        "voice.mp3"
    ])
    print("✅ voice.mp3 created")


# 🖼️ CREATE ANIMATED VIDEO (ZOOM + PAN)
def create_animated_video():
    print("🎬 Creating animated video")

    run([
        "ffmpeg", "-y",

        # 🎥 animated gradient background
        "-f", "lavfi",
        "-i", "color=c=black:s=1280x720:d=600",

        # 🔊 audio
        "-i", "voice.mp3",

        # 🎞️ animation
        "-vf",
        (
            "zoompan="
            "z='1.0+0.001*on':"
            "x='iw/2-(iw/zoom/2)':"
            "y='ih/2-(ih/zoom/2)':"
            f"d={FPS}"
        ),

        "-r", str(FPS),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-t", str(VIDEO_DURATION),
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",
        "final.mp4"
    ])

    print("✅ final.mp4 created (animated)")


# 🔐 YOUTUBE AUTH (BASE64 TOKEN)
def get_authenticated_service():
    print("🔐 Authenticating YouTube")

    if "YOUTUBE_TOKEN_BASE64" not in os.environ:
        raise RuntimeError("YOUTUBE_TOKEN_BASE64 secret missing")

    token_json = base64.b64decode(
        os.environ["YOUTUBE_TOKEN_BASE64"]
    ).decode("utf-8")

    creds = Credentials.from_authorized_user_info(
        json.loads(token_json),
        scopes=["https://www.googleapis.com/auth/youtube.upload"]
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
                "description": "An animated AI-generated documentary",
                "tags": ["Stonehenge", "History", "Mystery"],
                "categoryId": "27"
            },
            "status": {
                "privacyStatus": "public"
            }
        },
        media_body=MediaFileUpload(
            "final.mp4",
            chunksize=-1,
            resumable=True
        )
    )

    response = request.execute()
    print("✅ Uploaded:", response["id"])


def main():
    print("🚀 Starting full animated video pipeline")

    create_audio()
    create_animated_video()
    upload_video()


if __name__ == "__main__":
    main()