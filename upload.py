import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

def upload_video(video_file, title, is_short=False):
    api_key = os.environ.get("YOUTUBE_API_KEY")

    youtube = build(
        "youtube",
        "v3",
        developerKey=api_key
    )

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
    print("Uploaded video ID:", response["id"])