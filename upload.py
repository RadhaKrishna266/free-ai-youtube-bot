import os
import subprocess
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ================= CONFIG =================
TOPIC = "Mystery of Stonehenge"
TITLE = "Mystery of Stonehenge | Full Documentary"
DESCRIPTION = "A detailed AI-generated documentary on Stonehenge."
TAGS = ["stonehenge", "history", "documentary"]
CATEGORY_ID = "27"  # Education
VIDEO_FILE = "final.mp4"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
# ==========================================

def generate_script():
    print("📝 Generating long script...")
    text = (
        "Stonehenge is one of the most mysterious monuments on Earth. "
        "Located in England, this ancient stone circle has puzzled historians for centuries. "
        "Researchers believe it was built over several phases. "
        "The stones align with the solstices, suggesting astronomical importance. "
        "Some theories claim it was a burial site, others say a healing center. "
        "Despite modern technology, many questions remain unanswered. "
    ) * 70  # ~7–9 minutes

    with open("script.txt", "w") as f:
        f.write(text)

def generate_voice():
    print("🎤 Generating voice...")
    subprocess.run([
        "edge-tts",
        "--voice", "en-IN-PrabhatNeural",
        "--file", "script.txt",
        "--write-media", "voice.mp3"
    ], check=True)

def get_audio_duration():
    print("⏱ Getting audio duration...")
    result = subprocess.check_output([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        "voice.mp3"
    ])
    return float(result.strip())

def generate_images():
    print("🖼 Creating images...")
    os.makedirs("images", exist_ok=True)
    for i in range(1, 11):
        subprocess.run([
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", "color=c=black:s=1920x1080",
            "-frames:v", "1",
            f"images/img{i}.png"
        ], check=True)

def generate_video(audio_duration):
    print("🎞 Creating video...")
    per_image = audio_duration / 10

    with open("images.txt", "w") as f:
        for i in range(1, 11):
            f.write(f"file 'images/img{i}.png'\n")
            f.write(f"duration {per_image}\n")

    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", "images.txt",
        "-vf", "scale=1920:1080,format=yuv420p",
        "-r", "25",
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

def get_authenticated_service():
    print("🔐 Authenticating YouTube...")
    secret_json = os.environ["YOUTUBE_CLIENT_SECRET"]
    with open("client_secret.json", "w") as f:
        f.write(secret_json)

    flow = InstalledAppFlow.from_client_secrets_file(
        "client_secret.json", SCOPES
    )
    creds = flow.run_console()
    return build("youtube", "v3", credentials=creds)

def upload_to_youtube():
    print("⬆ Uploading to YouTube...")
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
                "privacyStatus": "public"
            }
        },
        media_body=MediaFileUpload(VIDEO_FILE)
    )
    response = request.execute()
    print("✅ Uploaded Video ID:", response["id"])

def main():
    print("🚀 Starting pipeline")
    generate_script()
    generate_voice()
    duration = get_audio_duration()
    print(f"🎯 Video length: {int(duration//60)} minutes")
    generate_images()
    generate_video(duration)
    upload_to_youtube()
    print("🎉 DONE")

if __name__ == "__main__":
    main()