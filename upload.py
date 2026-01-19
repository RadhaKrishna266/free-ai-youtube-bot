import os
import json
import base64
import subprocess
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

VIDEO_FILE = "final.mp4"

def run(cmd):
    subprocess.run(cmd, check=True)

# -----------------------------
# VIDEO GENERATION
# -----------------------------
def create_silent_audio():
    if os.path.exists("voice.mp3"):
        return
    print("🔊 Creating silent voice.mp3 (10 minutes)")
    run([
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "anullsrc=r=44100:cl=stereo",
        "-t", "600",
        "voice.mp3"
    ])
    print("✅ voice.mp3 created")

def create_background():
    print("🖼️ Creating background image")
    run([
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "color=c=black:s=1280x720",
        "-frames:v", "1",
        "bg.jpg"
    ])

def create_video():
    print("🎬 Creating animated video")
    run([
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", "bg.jpg",
        "-i", "voice.mp3",
        "-vf", "zoompan=z='min(zoom+0.0003,1.15)':d=125",
        "-t", "600",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-shortest",
        "final.mp4"
    ])
    print("✅ final.mp4 created")

# -----------------------------
# YOUTUBE AUTH (BASE64 TOKEN)
# -----------------------------
def get_authenticated_service():
    print("🔐 Authenticating YouTube (BASE64 TOKEN)")

    token_b64 = os.getenv("YOUTUBE_TOKEN_BASE64")
    if not token_b64:
        raise RuntimeError("YOUTUBE_TOKEN_BASE64 secret missing")

    token_json = base64.b64decode(token_b64).decode("utf-8")

    with open("token.json", "w") as f:
        f.write(token_json)

    creds = Credentials.from_authorized_user_file(
        "token.json",
        scopes=["https://www.googleapis.com/auth/youtube.upload"]
    )

    return build("youtube", "v3", credentials=creds)

# -----------------------------
# UPLOAD VIDEO
# -----------------------------
def upload_video():
    youtube = get_authenticated_service()

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": "The Mystery of Stonehenge",
                "description": "An AI-generated documentary video.",
                "tags": ["Stonehenge", "history", "AI video"],
                "categoryId": "22"
            },
            "status": {
                "privacyStatus": "public"
            }
        },
        media_body=MediaFileUpload(VIDEO_FILE, chunksize=-1, resumable=True)
    )

    response = request.execute()
    print("🎉 Uploaded successfully!")
    print("📺 Video ID:", response["id"])

# -----------------------------
# MAIN
# -----------------------------
def main():
    print("🚀 Starting full animated video pipeline")
    create_silent_audio()
    create_background()
    create_video()
    upload_video()

if __name__ == "__main__":
    main()