import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

def upload_video(video_file, title, is_short=False):
    api_key = os.environ.get("YOUTUBE_API_KEY")

    from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import pickle
import os

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def get_youtube_service():
    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            "client_secret.json", SCOPES
        )
        creds = flow.run_console()
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    return build("youtube", "v3", credentials=creds)
    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": title[:90],
                "description": f"{title}\n\n#facts #history #technology",
                "tags": ["facts", "history", "technology"],
                "categoryId": "27"
            },
            "status": {
                "privacyStatus": "public"
            }
        },
        media_body=MediaFileUpload(video_file)
    )

    response = request.execute()
    print("✅ Uploaded video ID:", response["id"])