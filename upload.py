import os
import json
import subprocess
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

# ================= CONFIG =================
VIDEO_FILE = "final.mp4"
TITLE = "The Mystery of Stonehenge"
DESCRIPTION = "An AI-generated animated documentary about Stonehenge."
TAGS = ["Stonehenge", "History", "Ancient", "AI Documentary"]
CATEGORY_ID = "27"  # Education
PRIVACY = "public"

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

# =========================================


def run(cmd):
    subprocess.run(cmd, check=True)


# ---------- AUTH (GITHUB ACTIONS SAFE) ----------
def get_authenticated_service():
    print("🔐 Authenticating YouTube (token-based)...")

    token_json = os.environ.get("YOUTUBE_TOKEN_JSON")
    if not token_json:
        raise RuntimeError("YOUTUBE_TOKEN_JSON secret missing")

    creds_info = json.loads(token_json)
    creds = Credentials.from_authorized_user_info(creds_info, SCOPES)

    return build("youtube", "v3", credentials=creds)


# ---------- VIDEO CREATION (ANIMATED) ----------
def create_animated_video():
    print("🎬 Creating animated video background...")

    run([
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", "images/bg.jpg",
        "-i", "voice.mp3",
        "-vf", "zoompan=z='min(zoom+0.0005,1.15)':d=25",
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-pix_fmt", "yuv420p",
        "-shortest",
        VIDEO_FILE
    ])

    print("✅ final.mp4 created")


# ---------- UPLOAD ----------
def upload_to_youtube():
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
                "privacyStatus": PRIVACY
            }
        },
        media_body=MediaFileUpload(
            VIDEO_FILE,
            chunksize=-1,
            resumable=True
        )
    )

    response = request.execute()
    print(f"✅ Uploaded successfully: https://youtu.be/{response['id']}")


# ---------- MAIN ----------
def main():
    print("🚀 Starting full animated video pipeline")

    if not os.path.exists(VIDEO_FILE):
        create_animated_video()

    upload_to_youtube()


if __name__ == "__main__":
    main()