import os
import json
import base64
import subprocess
import requests
from pathlib import Path

from TTS.api import TTS
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# ================= CONFIG =================
SCRIPT_FILE = "script.txt"       # Your narration script
VOICE_SAMPLE = "speaker.wav"     # Short sample of your voice
FINAL_AUDIO = "final_audio.wav"
FINAL_VIDEO = "final_video.mp4"

IMAGE_DIR = "images"
TANPURA = "audio/tanpura.mp3"

TARGET_DURATION = 600  # 10 minutes = 600 seconds

YOUTUBE_SCOPE = "https://www.googleapis.com/auth/youtube.upload"

os.makedirs(IMAGE_DIR, exist_ok=True)

# ================= UTILS =================
def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)

def get_duration(path):
    out = subprocess.check_output([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        path
    ])
    return float(out.strip())

# ================= IMAGES =================
def download_images(count=20):
    print("🖼 Downloading divine images")

    r = requests.get(
        "https://pixabay.com/api/",
        params={
            "key": os.environ["PIXABAY_API_KEY"],
            "q": "Vishnu purana illustration divine",
            "image_type": "photo",
            "orientation": "horizontal",
            "per_page": count
        }
    ).json()

    hits = r.get("hits", [])
    if not hits:
        raise RuntimeError("No images returned from Pixabay")

    for i, hit in enumerate(hits):
        img = requests.get(hit["largeImageURL"]).content
        with open(f"{IMAGE_DIR}/{i:03d}.jpg", "wb") as f:
            f.write(img)

# ================= VOICE =================
def create_voice():
    print("🎙 Generating narration in your voice (XTTS-v2)")

    text = Path(SCRIPT_FILE).read_text(encoding="utf-8")

    tts = TTS(
        model_name="tts_models/multilingual/multi-dataset/xtts_v2",
        gpu=False
    )

    tts.tts_to_file(
        text=text,
        speaker_wav=VOICE_SAMPLE,
        file_path=FINAL_AUDIO
    )

# ================= AUDIO MIX =================
def mix_tanpura(target_duration=TARGET_DURATION):
    print("🎶 Mixing tanpura softly")

    narration_duration = get_duration(FINAL_AUDIO)
    final_duration = max(narration_duration, target_duration)

    run([
        "ffmpeg", "-y",
        "-i", FINAL_AUDIO,
        "-stream_loop", "-1", "-i", TANPURA,
        "-filter_complex",
        f"[1:a]volume=0.15,atrim=0:{final_duration}[bg];[0:a][bg]amix=inputs=2",
        "-t", str(final_duration),
        FINAL_AUDIO
    ])

    return final_duration

# ================= VIDEO =================
def create_video(duration):
    print("🎞 Creating video")

    image_files = os.listdir(IMAGE_DIR)
    if not image_files:
        raise RuntimeError("No images found in IMAGE_DIR")

    # Spread images evenly over duration
    framerate = len(image_files) / duration  # images per second

    run([
        "ffmpeg", "-y",
        "-framerate", str(framerate),
        "-pattern_type", "glob",
        "-i", f"{IMAGE_DIR}/*.jpg",
        "-i", FINAL_AUDIO,
        "-t", str(duration),
        "-vf", "scale=1280:720,format=yuv420p",
        "-c:v", "libx264",
        "-preset", "slow",
        "-c:a", "aac",
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
        refresh_token=token_info.get("refresh_token"),
        token_uri=token_info["token_uri"],
        client_id=token_info["client_id"],
        client_secret=token_info["client_secret"],
        scopes=[YOUTUBE_SCOPE]
    )

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

    youtube = build("youtube", "v3", credentials=creds)

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": "विष्णु पुराण | अध्याय 1 | Sanatan Gyaan Dhara",
                "description": (
                    "॥ श्री विष्णु पुराण ॥\n\n"
                    "Sanatan Gyaan Dhara में आपका स्वागत है।\n"
                    "हम प्रतिदिन विष्णु पुराण के अध्याय प्रस्तुत करेंगे।\n\n"
                    "🙏 कृपया चैनल को सब्सक्राइब करें\n"
                    "🔔 वीडियो को लाइक और शेयर करें\n"
                ),
                "categoryId": "22"
            },
            "status": {
                "privacyStatus": "public"
            }
        },
        media_body=MediaFileUpload(
            FINAL_VIDEO,
            mimetype="video/mp4",
            resumable=True
        )
    )

    response = request.execute()
    print("✅ Uploaded. Video ID:", response["id"])

# ================= MAIN =================
def main():
    download_images()
    create_voice()
    duration = mix_tanpura()
    create_video(duration)
    upload_youtube()

if __name__ == "__main__":
    main()