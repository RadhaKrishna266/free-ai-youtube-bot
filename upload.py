import os
import json
from pathlib import Path
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

# Try common output names
VIDEO_CANDIDATES = ["output.mp4", "final.mp4"]


def find_video():
    for name in VIDEO_CANDIDATES:
        for path in Path(".").rglob(name):
            return path
    return None


def load_credentials():
    raw = os.environ.get("YOUTUBE_CLIENT_SECRET")
    if not raw:
        raise RuntimeError("YOUTUBE_CLIENT_SECRET is not set")

    try:
        info = json.loads(raw)
    except json.JSONDecodeError:
        raise RuntimeError("YOUTUBE_CLIENT_SECRET is not valid JSON")

    required = {"client_id", "client_secret", "refresh_token", "token_uri"}
    missing = required - info.keys()
    if missing:
        raise RuntimeError(f"Missing OAuth fields: {missing}")

    return Credentials.from_authorized_user_info(info, SCOPES)


def upload_video(video_path: Path):
    creds = load_credentials()
    youtube = build("youtube", "v3", credentials=creds)

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": "Mystery of Stonehenge",
                "description": (
                    "A 10+ minute documentary exploring the mystery of Stonehenge, "
                    "its origins, theories, and historical significance."
                ),
                "tags": ["history", "documentary", "ancient", "mystery"],
                "categoryId": "27"
            },
            "status": {
                "privacyStatus": "public"
            }
        },
        media_body=MediaFileUpload(
            str(video_path),
            chunksize=-1,
            resumable=True
        ),
    )

    response = request.execute()
    return response["id"]


if __name__ == "__main__":
    print("🔍 Searching for video file...")
    video = find_video()

    if not video:
        print("❌ No video file found (output.mp4 / final.mp4)")
        print("📂 Files present:")
        for f in Path(".").rglob("*.mp4"):
            print(" -", f)
        raise SystemExit(1)

    print(f"✅ Found video: {video}")

    try:
        video_id = upload_video(video)
        print(f"🎉 Uploaded successfully: https://youtu.be/{video_id}")
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        raise