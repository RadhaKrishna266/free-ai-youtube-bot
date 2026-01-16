import os
import json
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def get_youtube_service():
    creds = None

    # Rebuild client_secret.json from env
    if not os.path.exists("client_secret.json"):
        secret_json = os.environ.get("YOUTUBE_CLIENT_SECRET")
        if not secret_json:
            raise Exception("Missing YOUTUBE_CLIENT_SECRET env variable")

        with open("client_secret.json", "w") as f:
            f.write(secret_json)

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