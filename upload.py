import os
import json
import base64
import subprocess
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

# ================= CONFIG =================
VIDEO_FILE = "final.mp4"
VOICE_FILE = "voice.mp3"
BG_IMAGE = "bg.jpg"
DURATION_SECONDS = 600  # 10 minutes
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

TITLE = "The Mystery of Stonehenge"
DESCRIPTION = "An AI-generated documentary with animated visuals and narration."
TAGS = ["Stonehenge", "History", "Mystery", "AI video"]
CATEGORY_ID = "27"  # Education
# ==========================================


def run(cmd):
    subprocess.run(cmd, check=True)


# ---------- AUDIO ----------
def create_voice():
    if os.path.exists(VOICE_FILE):
        return
    print("🔊 Creating silent voice.mp3 (10 minutes)")
    run([
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "anullsrc=r=44100:cl=stereo",
        "-t", str(DURATION_SECONDS),
        VOICE_FILE
    ])
    print("✅ voice.mp3 created")


# ---------- IMAGE ----------
def create_background():
    if os.path.exists(BG_IMAGE):
        return
    print("🖼️ Creating background image")
    run([
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "color=c=darkslategray:s=1920x1080",
        "-frames:v", "1",
        BG_IMAGE
    ])


# ---------- VIDEO ----------
def create_video():
    if os.path.exists(VIDEO_FILE):
        return
    print("🎬 Creating animated video")
    run([
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", BG_IMAGE,
        "-i", VOICE_FILE,
        "-vf",
        "zoompan=z='min(zoom+0.0003,1.15)':d=125,scale=1920:1080",
        "-t", str(DURATION_SECONDS),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-shortest",
        VIDEO_FILE
    ])
    print("✅ final.mp4 created")


# ---------- AUTH ----------
def get_authenticated_service():
    print("🔐 Authenticating YouTube")

    # Preferred: BASE64 token
    if "YOUTUBE_TOKEN_BASE64" in os.environ:
        token_json = base64.b64decode(
            os.environ["YOUTUBE_TOKEN_BASE64"]
        ).decode()
    else:
        token_json = os.environ["YOUTUBE_TOKEN_JSON"]

    creds = Credentials.from_authorized_user_info(
        json.loads(token_json),
        SCOPES
    )

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
                "categoryId": CATEGORY_ID
            },
            "status": {
                "privacyStatus": "public"
            }
        },
        media_body=MediaFileUpload(
            VIDEO_FILE,
            chunksize=-1,
            resumable=True
        )
    )

    response = request.execute()
    print("🚀 Upload successful!")
    print("🎥 Video ID:", response["id"])


# ---------- MAIN ----------
def main():
    print("🚀 Starting full animated video pipeline")
    create_voice()
    create_background()
    create_video()
    upload_video()


if __name__ == "__main__":
    main()