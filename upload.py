import os
import json
import subprocess
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

VIDEO_FILE = "final.mp4"
VOICE_FILE = "voice.mp3"
BG_IMAGE = "bg.jpg"

TITLE = "The Mystery of Stonehenge"
DESCRIPTION = "An AI-generated animated documentary about Stonehenge."
TAGS = ["Stonehenge", "History", "Ancient"]
CATEGORY_ID = "27"
PRIVACY = "public"

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def run(cmd):
    subprocess.run(cmd, check=True)


# ---------- CREATE BACKGROUND IMAGE ----------
def create_background():
    if os.path.exists(BG_IMAGE):
        return

    print("🖼️ Creating fallback background image...")
    run([
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "color=c=darkslategray:s=1280x720",
        "-frames:v", "1",
        BG_IMAGE
    ])


# ---------- CREATE ANIMATED VIDEO ----------
def create_video():
    print("🎬 Creating animated video...")
    create_background()

    run([
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", BG_IMAGE,
        "-i", VOICE_FILE,
        "-vf",
        "zoompan=z='min(zoom+0.0015,1.2)':d=25,scale=1280:720",
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-pix_fmt", "yuv420p",
        "-shortest",
        VIDEO_FILE
    ])

    print("✅ final.mp4 created")


# ---------- AUTH ----------
def get_authenticated_service():
    print("🔐 Authenticating YouTube...")

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
                "categoryId": CATEGORY_ID
            },
            "status": {"privacyStatus": PRIVACY}
        },
        media_body=MediaFileUpload(VIDEO_FILE, resumable=True)
    )

    response = request.execute()
    print(f"✅ Uploaded: https://youtu.be/{response['id']}")


# ---------- MAIN ----------
def main():
    print("🚀 Starting full animated video pipeline")

    if not os.path.exists(VOICE_FILE):
        raise RuntimeError("voice.mp3 missing")

    create_video()
    upload_video()


if __name__ == "__main__":
    main()