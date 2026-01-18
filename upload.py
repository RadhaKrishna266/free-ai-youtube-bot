import os
import json
import pickle
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# -----------------------------
# CONFIG
# -----------------------------
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
CLIENT_SECRET_FILE = "client_secret.json"
TOKEN_FILE = "token.json"

# -----------------------------
# AUTHENTICATION
# -----------------------------
def get_authenticated_service():
    creds = None

    # token.json MUST exist (created by GitHub Actions)
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # Refresh or create token if needed
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRET_FILE, SCOPES
            )
            creds = flow.run_console()

        # Save token.json (for local runs)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return build("youtube", "v3", credentials=creds)


# -----------------------------
# VIDEO UPLOAD
# -----------------------------
def upload_video(
    video_file,
    title,
    description,
    tags,
    category_id="27",  # Education
    privacy_status="public",
):
    youtube = get_authenticated_service()

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": privacy_status,
        },
    }

    media = MediaFileUpload(
        video_file,
        chunksize=-1,
        resumable=True,
        mimetype="video/mp4",
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Upload progress: {int(status.progress() * 100)}%")

    print("✅ Upload complete!")
    print("🎬 Video ID:", response["id"])


# -----------------------------
# EXAMPLE CALL
# -----------------------------
if __name__ == "__main__":
    upload_video(
        video_file="output.mp4",
        title="Test Video Upload",
        description="This video was uploaded automatically.",
        tags=["facts", "history", "tech", "ai"],
    )