import os
import json
from pathlib import Path
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def find_video(filename="final.mp4"):
    """
    Recursively find final.mp4 anywhere in the repo
    """
    for path in Path(".").rglob(filename):
        return path
    return None


def load_credentials():
    raw = os.environ.get("YOUTUBE_CLIENT_SECRET")
    if not raw:
        raise RuntimeError("YOUTUBE_CLIENT_SECRET not set")

    info = json.loads(raw)

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
                "description": "Complete documentary about the Mystery of Stonehenge.",
                "tags": ["history", "mystery", "documentary"],
                "categoryId": "22",
            },
            "status": {
                "privacyStatus": "public",
            },
        },
        media_body=MediaFileUpload(
            str(video_path),
            chunksize=-1,
            resumable=True,
        ),
    )

    response = request.execute()
    return response["id"]


if __name__ == "__main__":
    print("🔍 Searching for final.mp4 ...")
    video = find_video()

    if not video:
        print("❌ final.mp4 not found anywhere in repository")
        print("📂 Files present:")
        for p in Path(".").rglob("*"):
            if p.is_file():
                print(" -", p)
        raise SystemExit(1)

    print(f"✅ Found video at: {video}")

    try:
        video_id = upload_video(video)
        print(f"🎉 Uploaded successfully: https://youtu.be/{video_id}")
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        raise