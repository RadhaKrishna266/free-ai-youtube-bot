import os
import json
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials


SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
VIDEO_FILE = "final.mp4"


def load_credentials():
    """
    Loads OAuth credentials from GitHub secret:
    YOUTUBE_CLIENT_SECRET (full authorized user JSON)
    """
    raw = os.environ.get("YOUTUBE_CLIENT_SECRET")

    if not raw:
        raise RuntimeError("YOUTUBE_CLIENT_SECRET not set")

    try:
        info = json.loads(raw)
    except json.JSONDecodeError:
        raise RuntimeError("YOUTUBE_CLIENT_SECRET is not valid JSON")

    required = {"client_id", "client_secret", "refresh_token", "token_uri"}
    missing = required - info.keys()

    if missing:
        raise RuntimeError(f"Missing OAuth fields: {missing}")

    return Credentials.from_authorized_user_info(info, SCOPES)


def upload_video(
    title,
    description,
    tags=None,
    category_id="22",
    privacy="public",
):
    if not os.path.exists(VIDEO_FILE):
        raise FileNotFoundError(f"{VIDEO_FILE} not found")

    creds = load_credentials()
    youtube = build("youtube", "v3", credentials=creds)

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags or [],
                "categoryId": category_id,
            },
            "status": {
                "privacyStatus": privacy,
            },
        },
        media_body=MediaFileUpload(
            VIDEO_FILE,
            chunksize=-1,
            resumable=True,
        ),
    )

    response = request.execute()
    return response["id"]


if __name__ == "__main__":
    try:
        video_id = upload_video(
            title="Mystery of Stonehenge",
            description="Complete documentary about the Mystery of Stonehenge.",
            tags=["history", "mystery", "documentary"],
        )
        print(f"✅ Uploaded successfully: https://youtu.be/{video_id}")

    except Exception as e:
        print(f"❌ Upload failed: {e}")