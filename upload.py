import os
import json
import base64
import subprocess
import requests
from pathlib import Path

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from TTS.api import TTS

# ================= CONFIG =================
SCRIPT_FILE = "script.txt"
VOICE_FILE = "narration.wav"
FINAL_VIDEO = "final.mp4"

IMAGE_DIR = "images"
IMAGE_COUNT = 6

# CALM SINGLE-SPEAKER HINDI MODEL
MODEL = "tts_models/hi/mai/tacotron2-DDC"

YOUTUBE_SCOPE = "https://www.googleapis.com/auth/youtube.upload"

# ================= UTILS =================
def run(cmd):
    subprocess.run(cmd, check=True)

# ================= IMAGES =================
def download_images():
    print("🖼 Downloading divine images")
    os.makedirs(IMAGE_DIR, exist_ok=True)

    for i in range(IMAGE_COUNT):
        r = requests.get(
            "https://pixabay.com/api/",
            params={
                "key": os.environ["PIXABAY_API_KEY"],
                "q": "Vishnu Narayan painting",
                "orientation": "horizontal",
                "per_page": 20,
                "safesearch": "true"
            }
        ).json()

        img_url = r["hits"][i]["largeImageURL"]
        img = requests.get(img_url).content

        with open(f"{IMAGE_DIR}/{i:03}.jpg", "wb") as f:
            f.write(img)

# ================= AUDIO =================
def create_audio():
    print("🎙 Creating calm divine narration")

    text = Path(SCRIPT_FILE).read_text(encoding="utf-8")

    tts = TTS(model_name=MODEL, gpu=False)
    tts.tts_to_file(
        text=text,
        file_path=VOICE_FILE
    )

# ================= VIDEO =================
def create_video():
    print("🎬 Creating slideshow video")

    with open("images.txt", "w") as f:
        for i in range(IMAGE_COUNT):
            f.write(f"file '{IMAGE_DIR}/{i:03}.jpg'\n")
            f.write("duration 6\n")

    run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", "images.txt",
        "-i", VOICE_FILE,
        "-vsync", "vfr",
        "-pix_fmt", "yuv420p",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-shortest",
        FINAL_VIDEO
    ])

# ================= YOUTUBE =================
def upload_youtube():
    print("📤 Uploading to YouTube")

    token_info = json.loads(
        base64.b64decode(os.environ["YOUTUBE_TOKEN_BASE64"]).decode("utf-8")
    )

    creds = Credentials(
        token=token_info["token"],
        refresh_token=token_info["refresh_token"],
        token_uri=token_info["token_uri"],
        client_id=token_info["client_id"],
        client_secret=token_info["client_secret"],
        scopes=[YOUTUBE_SCOPE]
    )

    if creds.expired:
        creds.refresh(Request())

    youtube = build("youtube", "v3", credentials=creds)

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": "विष्णु पुराण | अध्याय 1 | Sanatan Gyaan Dhara",
                "description": (
                    "विष्णु पुराण – अध्याय 1\n\n"
                    "Sanatan Gyaan Dhara पर प्रतिदिन पावन ग्रंथों का दिव्य पाठ।\n\n"
                    "यदि वीडियो अच्छा लगे तो Like, Share और Subscribe अवश्य करें।\n\n"
                    "ॐ नमो नारायणाय 🙏"
                ),
                "categoryId": "22"
            },
            "status": {
                "privacyStatus": "public"
            }
        },
        media_body=MediaFileUpload(FINAL_VIDEO, resumable=True)
    )

    response = request.execute()
    print("✅ Uploaded successfully:", response["id"])

# ================= MAIN =================
def main():
    download_images()
    create_audio()
    create_video()
    upload_youtube()

if __name__ == "__main__":
    main()