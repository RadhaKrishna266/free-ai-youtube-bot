import os
import json
import subprocess
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

VIDEO_FILE = "final.mp4"
VOICE_FILE = "voice.mp3"
BG_IMAGE = "bg.jpg"

DURATION_SECONDS = 600  # 10 minutes

TITLE = "The Mystery of Stonehenge"
DESCRIPTION = "An AI-generated animated documentary about Stonehenge."
TAGS = ["Stonehenge", "Ancient History", "Mystery"]
CATEGORY_ID = "27"
PRIVACY = "public"

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def run(cmd):
    subprocess.run(cmd, check=True)


# ---------- VOICE (AUTO-GENERATED SILENT FALLBACK) ----------
def generate_voice():
    if os.path.exists(VOICE_FILE):
        print("🔊 voice.mp3 already exists")
        return

    print("🔊 Creating silent voice.mp3 (10 minutes)")
    run([
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"anullsrc=r=44100:cl=stereo",
        "-t", str(DURATION_SECONDS),
        "-q:a", "9",
        VOICE_FILE
    ])
    print("✅ voice.mp3 created")


# ---------- BACKGROUND IMAGE ----------
def create_background():
    if os.path.exists(BG_IMAGE):
        return

    print("🖼️ Creating background image")
    run([
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "color=c=darkslategray:s=1280x720",
        "-frames:v", "1",
        BG_IMAGE
    ])


# ---------- ANIMATED VIDEO ----------
def create_video():
    print("🎬 Creating animated video")
    create_background()

    run([
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", BG_IMAGE,
        "-i", VOICE_FILE,
        "-vf",
        "zoompan=z='min(zoom+0.001,1.25)':d=25,scale=1280:720",
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-pix_fmt", "yuv420p",
        "-shortest",
        VIDEO_FILE
    ])

    print("✅ final.mp4 created")


# ---------- YOUTUBE AUTH ----------
def get_authenticated_service():
    print("🔐 Authenticating YouTube")

    token_json = os.environ["YOUTUBE_TOKEN_JSON"]
    creds_info = json.loads(token_json)
    creds = Credentials.from_authorized_user_info(creds_info, SCOPES)

    return build("youtube", "v3", credentials=creds)


# ---------- UPLOAD ----------
def upload_video():
    youtube = get_authenticated_service()

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": TITLE,
                "description": DESCRIPTION,
                "tags": TAGS,
                "categoryId": CATEGORY_ID,
            },
            "status": {"privacyStatus": PRIVACY},
        },
        media_body=MediaFileUpload(VIDEO_FILE, resumable=True),
    )

    response = request.execute()
    print(f"✅ Uploaded: https://youtu.be/{response['id']}")


# ---------- MAIN ----------
def main():
    print("🚀 Starting full animated video pipeline")

    generate_voice()
    create_video()
    upload_video()


if __name__ == "__main__":
    main()