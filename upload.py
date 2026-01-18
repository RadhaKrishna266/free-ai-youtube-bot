import os
import pickle
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def upload_video(video_path, title, is_short=False):
    print("Uploading:", video_path)

    if is_short:
        category = "short"
        tags = ["shorts", "facts", "history", "tech"]
    else:
        category = "long"
        tags = ["education", "facts", "history", "technology"]

    # Title handling
    if is_short:
        final_title = title[:90]
    else:
        final_title = title

    print("Video type:", category)
    print("Title:", final_title)

    # TODO: YouTube API upload logic here

