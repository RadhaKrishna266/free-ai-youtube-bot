import os
import json
import subprocess
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

VIDEO_FILE = "final.mp4"
VOICE_FILE = "voice.mp3"
TEMP_VIDEO = "video.mp4"

VIDEO_DURATION = 600  # 600 sec = 10 min (change to 300 for 5 min)

# -----------------------------
# CREATE VIDEO (NO IMAGES NEEDED)
# -----------------------------
def create_video():
    print("🎬 Creating video...")

    # Animated gradient background (safe & fast)
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "color=c=black:s=1920x1080:r=25",
        "-vf", "geq=r='X/W*255':g='Y/H*255':b='128'",
        "-t", str(VIDEO_DURATION),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        TEMP_VIDEO
    ], check=True)

    # Merge audio + video (RE-ENCODE video → avoids crash)
    subprocess.run([
        "ffmpeg", "-y",
        "-i", TEMP_VIDEO,
        "-i", VOICE_FILE,
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "libx264",
        "-preset", "fast",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-shortest",
        VIDEO_FILE
    ], check=True)

    print("✅ Video created:", VIDEO_FILE)

# -----------------------------
# YOUTUBE AUTH
# -----------------------------
def get_authenticated_service():
    print("🔐 Authenticating YouTube...")

    client_secret = json.loads(os.environ["YOUTUBE_CLIENT_SECRET"])
    token_info = json.loads(os.environ["YOUTUBE_TOKEN_JSON"])

    creds = Credentials(
        token=token_info["token"],
        refresh_token=token_info["refresh_token"],
        token_uri=token_info["token_uri"],
        client_id=client_secret["installed"]["client_id"],
        client_secret=client_secret["installed"]["client_secret"],
        scopes=["https://www.googleapis.com/auth/youtube.upload"]
    )

    return build("youtube", "v3", credentials=creds)

# -----------------------------
# UPLOAD TO YOUTUBE
# -----------------------------
def upload_to_youtube():
    youtube = get_authenticated_service()

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": "Mystery of Stonehenge",
                "description": "Auto-generated documentary video",
                "tags": ["mystery", "history", "documentary"],
                "categoryId": "22"
            },
            "status": {
                "privacyStatus": "public"
            }
        },
        media_body=MediaFileUpload(VIDEO_FILE, resumable=True)
    )

    response = request.execute()
    print("🚀 Uploaded successfully!")
    print("📺 Video ID:", response["id"])

# -----------------------------
# MAIN
# -----------------------------
def main():
    if not os.path.exists(VOICE_FILE):
        raise FileNotFoundError("❌ voice.mp3 not found")

    create_video()
    upload_to_youtube()

if __name__ == "__main__":
    main()