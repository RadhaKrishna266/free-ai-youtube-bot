import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def upload_video(video_file, title, is_short):
    flow = InstalledAppFlow.from_client_secrets_file(
            "client_secret.json", SCOPES
                )
                    credentials = flow.run_console()

                        youtube = build("youtube", "v3", credentials=credentials)

                            request = youtube.videos().insert(
                                    part="snippet,status",
                                            body={
                                                        "snippet": {
                                                                        "title": title,
                                                                                        "description": title,
                                                                                                        "categoryId": "27"
                                                                                                                    },
                                                                                                                                "status": {
                                                                                                                                                "privacyStatus": "public"
                                                                                                                                                            }
                                                                                                                                                                    },
                                                                                                                                                                            media_body=MediaFileUpload(video_file)
                                                                                                                                                                                )

                                                                                                                                                                                    request.execute()