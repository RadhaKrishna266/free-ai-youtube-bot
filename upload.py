import os
import json
import googleapiclient.discovery
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def get_youtube_service():
    """
    Creates authenticated YouTube service using token stored in GitHub secret
    """
    token_json = os.environ.get("YOUTUBE_TOKEN_JSON")

    if not token_json:
        raise Exception("YOUTUBE_TOKEN_JSON secret not found")

    credentials_info = json.loads(token_json)

    from google.oauth2.credentials import Credentials
    creds = Credentials.from_authorized_user_info(credentials_info, SCOPES)

    youtube = googleapiclient.discovery.build(
        "youtube", "v3", credentials=creds
    )

    return youtube


def upload_video(video_path, title, description="", is_short=False):
    print("Uploading:", video_path)

    youtube = get_youtube_service()

    # Tags & category
    if is_short:
        tags = ["shorts", "facts", "history", "tech"]
        final_title = title[:90]  # Shorts title limit
    else:
        tags = ["education", "facts", "history", "technology"]
        final_title = title

    body = {
        "snippet": {
            "title": final_title,
            "description": description,
            "tags": tags,
            "categoryId": "27"  # Education
        },
        "status": {
            "privacyStatus": "public"
        }
    }

    media = MediaFileUpload(
        video_path,
        chunksize=-1,
        resumable=True,
        mimetype="video/*"
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )

    response = request.execute()

    print("Upload complete!")
    print("Video ID:", response["id"])