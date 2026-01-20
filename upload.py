import os
import json
import base64
import subprocess
import requests
from gtts import gTTS
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

DURATION_PER_SCENE = 8
FACTS = [
    "Octopuses have three hearts",
    "Honey never spoils",
    "Sharks existed before trees",
    "Bananas are berries",
    "Wombat poop is cube shaped"
]

PIXABAY_KEY = os.environ["PIXABAY_API_KEY"]


def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)


# 🎤 VOICE
def create_voice():
    text = "Unknown facts you never knew. " + ". ".join(FACTS)
    gTTS(text=text, lang="en").save("voice.mp3")
    print("✅ voice.mp3 created")


# 🖼️ DOWNLOAD IMAGES
def download_images():
    os.makedirs("images", exist_ok=True)

    for i, fact in enumerate(FACTS):
        query = fact.split()[0]
        url = (
            f"https://pixabay.com/api/?key={PIXABAY_KEY}"
            f"&q={query}&image_type=photo&per_page=3"
        )

        r = requests.get(url).json()
        img_url = r["hits"][0]["largeImageURL"]

        img_path = f"images/{i}.jpg"
        with open(img_path, "wb") as f:
            f.write(requests.get(img_url).content)

        print(f"✅ Image downloaded for: {fact}")


# 🎬 ANIMATED VIDEO FROM IMAGES
def create_video():
    with open("list.txt", "w") as f:
        for i in range(len(FACTS)):
            f.write(f"file 'images/{i}.jpg'\n")
            f.write(f"duration {DURATION_PER_SCENE}\n")

    run([
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", "list.txt",
        "-vf",
        "zoompan=z='min(zoom+0.0005,1.1)':d=240,"
        "scale=1280:720,format=yuv420p",
        "-i", "voice.mp3",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-shortest",
        "final.mp4"
    ])

    print("✅ final.mp4 created (REAL images + animation)")


# 🔐 AUTH
def youtube_auth():
    token = base64.b64decode(os.environ["YOUTUBE_TOKEN_BASE64"]).decode()
    creds = Credentials.from_authorized_user_info(
        json.loads(token),
        ["https://www.googleapis.com/auth/youtube.upload"]
    )
    return build("youtube", "v3", credentials=creds)


# 🚀 UPLOAD (ONCE)
def upload():
    yt = youtube_auth()

    request = yt.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": "Unknown Facts You Never Knew",
                "description": "Animated facts video with images and narration",
                "categoryId": "27"
            },
            "status": {"privacyStatus": "public"}
        },
        media_body=MediaFileUpload(
            "final.mp4",
            mimetype="video/mp4",
            resumable=False
        )
    )

    response = request.execute()
    print("✅ Uploaded:", response["id"])


def main():
    create_voice()
    download_images()
    create_video()
    upload()


if __name__ == "__main__":
    main()