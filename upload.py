import os
import json
import subprocess
import googleapiclient.discovery
import googleapiclient.http
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

VIDEO_FILE = "final.mp4"
TITLE = "Mystery of Stonehenge"
DESCRIPTION = "An AI generated documentary about the mystery of Stonehenge."
TAGS = ["stonehenge", "mystery", "history", "documentary"]
CATEGORY_ID = "22"
PRIVACY_STATUS = "public"


# -------------------- VIDEO CREATION --------------------
def create_video():
    print("🎬 Creating video...")

    if os.path.exists("images") and len(os.listdir("images")) > 0:
        print("🖼 Using images folder")

        with open("images.txt", "w") as f:
            for img in sorted(os.listdir("images")):
                if img.lower().endswith((".png", ".jpg", ".jpeg")):
                    f.write(f"file 'images/{img}'\n")
                    f.write("duration 6\n")

        subprocess.run([
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", "images.txt",
            "-vf", "scale=1920:1080,zoompan=z='zoom+0.0005':d=150",
            "-r", "25",
            "video.mp4"
        ], check=True)

    else:
        print("⚠️ images/ not found → generating animated background")

        subprocess.run([
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", "color=c=black:s=1920x1080:r=25",
            "-vf", "drawtext=text='Mystery of Stonehenge':fontcolor=white:fontsize=72:x=(w-text_w)/2:y=(h-text_h)/2",
            "-t", "600",
            "video.mp4"
        ], check=True)

    subprocess.run([
        "ffmpeg", "-y",
        "-i", "video.mp4",
        "-i", "voice.mp3",
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        VIDEO_FILE
    ], check=True)

    print("✅ Video ready:", VIDEO_FILE)


# -------------------- YOUTUBE AUTH --------------------
def get_authenticated_service():
    print("🔐 Authenticating YouTube...")

    client_secret = json.loads(os.environ["YOUTUBE_CLIENT_SECRET"])
    token_json = os.environ.get("YOUTUBE_TOKEN_JSON")

    creds = None
    if token_json:
        creds = Credentials.from_authorized_user_info(json.loads(token_json), SCOPES)

    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_config(client_secret, SCOPES)
        creds = flow.run_console()
        print("🔑 SAVE THIS TOKEN AS YOUTUBE_TOKEN_JSON:")
        print(creds.to_json())

    return googleapiclient.discovery.build("youtube", "v3", credentials=creds)


# -------------------- UPLOAD --------------------
def upload_video():
    youtube = get_authenticated_service()

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": TITLE,
                "description": DESCRIPTION,
                "tags": TAGS,
                "categoryId": CATEGORY_ID
            },
            "status": {
                "privacyStatus": PRIVACY_STATUS
            }
        },
        media_body=googleapiclient.http.MediaFileUpload(
            VIDEO_FILE, chunksize=-1, resumable=True
        )
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"⬆️ Upload {int(status.progress() * 100)}%")

    print("🎉 UPLOADED!")
    print("🔗 https://youtube.com/watch?v=" + response["id"])


# -------------------- MAIN --------------------
def main():
    create_video()
    upload_video()


if __name__ == "__main__":
    main()