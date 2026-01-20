import os
import json
import base64
import subprocess
from gtts import gTTS
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

DURATION = 600
FPS = 30


FACTS = [
    "Octopuses have three hearts.",
    "Bananas are berries, strawberries are not.",
    "Honey never spoils.",
    "There are more trees on Earth than stars in the Milky Way.",
    "Sharks existed before trees.",
    "Your brain uses more energy than your muscles.",
    "Wombat poop is cube-shaped.",
    "A day on Venus is longer than a year on Venus."
]


def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)


# 🔊 REAL HUMAN VOICE (FREE)
def create_voice():
    print("🔊 Creating narration voice")
    text = "Unknown facts you probably did not know. " + ". ".join(FACTS)
    tts = gTTS(text=text, lang="en")
    tts.save("voice.mp3")
    print("✅ voice.mp3 created")


# 🎬 CARTOON-STYLE ANIMATED VIDEO
def create_video():
    print("🎬 Creating animated cartoon-style video")

    drawtext_filters = []
    start = 0
    duration_per_fact = DURATION // len(FACTS)

    for fact in FACTS:
        drawtext_filters.append(
            f"drawtext=text='{fact}':"
            f"fontcolor=white:fontsize=48:"
            f"x=(w-text_w)/2:y=(h-text_h)/2:"
            f"enable='between(t,{start},{start+duration_per_fact})'"
        )
        start += duration_per_fact

    vf = ",".join(drawtext_filters)

    run([
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"color=c=blue:s=1280x720:r={FPS}:d={DURATION}",
        "-i", "voice.mp3",
        "-vf", vf,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        "-c:a", "aac",
        "-shortest",
        "final.mp4"
    ])

    print("✅ final.mp4 created")


# 🔐 AUTH
def get_authenticated_service():
    token = base64.b64decode(os.environ["YOUTUBE_TOKEN_BASE64"]).decode()
    creds = Credentials.from_authorized_user_info(
        json.loads(token),
        ["https://www.googleapis.com/auth/youtube.upload"]
    )
    return build("youtube", "v3", credentials=creds)


# 🚀 UPLOAD (NO DUPLICATES)
def upload_video():
    youtube = get_authenticated_service()

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": "Unknown Facts You Never Knew",
                "description": "Animated educational video with narration",
                "tags": ["unknown facts", "education", "animation"],
                "categoryId": "27"
            },
            "status": {
                "privacyStatus": "public"
            }
        },
        media_body=MediaFileUpload(
            "final.mp4",
            mimetype="video/mp4",
            resumable=False   # 🚫 NO DUPLICATES
        )
    )

    response = request.execute()
    print("✅ Uploaded:", response["id"])


def main():
    create_voice()
    create_video()
    upload_video()


if __name__ == "__main__":
    main()