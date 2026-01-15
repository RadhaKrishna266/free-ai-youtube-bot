from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os

def upload_video(video_file, title, is_short=False):
    youtube = build(
        "youtube", "v3",
        developerKey=os.environ["YOUTUBE_API_KEY"]
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": title,
                "description": title,
                "tags": ["facts", "history", "tech"],
                "categoryId": "27"
            },
            "status": {
                "privacyStatus": "public"
            }
        },
        media_body=MediaFileUpload(video_file)
    )
    request.execute()