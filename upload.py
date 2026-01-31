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
SCRIPT_FILE = "script.txt"   # Phoneme-safe Episode 1 script

NARRATION_WAV = "narration.wav"
FINAL_AUDIO = "final_audio.wav"
FINAL_VIDEO = "final_video.mp4"

IMAGE_DIR = "images"
TANPURA = "audio_fixed/tanpura_fixed.mp3"
TARGET_DURATION = 600  # 10 minutes

YOUTUBE_SCOPE = "https://www.googleapis.com/auth/youtube.upload"

os.makedirs(IMAGE_DIR, exist_ok=True)

# ================= UTILS =================
def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)

# ================= IMAGES =================
def download_images(count=50):
    """Download relevant divine images from Pixabay"""
    print("🖼 Downloading divine images...")
    response = requests.get(
        "https://pixabay.com/api/",
        params={
            "key": os.environ["PIXABAY_API_KEY"],
            "q": "Lord Vishnu painting, Krishna childhood, Vishnu temple illustration",
            "image_type": "photo",
            "orientation": "horizontal",
            "per_page": count
        }
    ).json()

    hits = response.get("hits", [])
    if not hits:
        raise RuntimeError("No images returned from Pixabay API.")

    for i, hit in enumerate(hits):
        img_data = requests.get(hit["largeImageURL"]).content
        with open(f"{IMAGE_DIR}/{i:03d}.jpg", "wb") as f:
            f.write(img_data)

# ================= VOICE =================
def generate_narration():
    """Generate pure Hindi narration from phoneme-safe script"""
    print("🎙 Generating narration in Hindi...")
    text = Path(SCRIPT_FILE).read_text(encoding="utf-8")

    # TTS - no custom voice to avoid gibberish
    tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2", gpu=False)
    tts.tts_to_file(
        text=text,
        speaker_wav=None,  # ✅ No speaker.wav
        language="hi",
        file_path="narration_raw.wav",
        speed=1.0
    )

    # Normalize audio: mono + 24kHz
    run([
        "ffmpeg", "-y",
        "-i", "narration_raw.wav",
        "-ac", "1",
        "-ar", "24000",
        "-filter:a", "volume=1.0",
        NARRATION_WAV
    ])

# ================= AUDIO MIX =================
def mix_tanpura():
    """Mix narration with soft tanpura background"""
    print("🎶 Mixing tanpura...")
    temp_audio = "final_audio_temp.wav"

    run([
        "ffmpeg", "-y",
        "-i", NARRATION_WAV,
        "-stream_loop", "-1",
        "-i", TANPURA,
        "-filter_complex",
        f"[1:a]volume=0.12,atrim=0:{TARGET_DURATION}[bg];[0:a][bg]amix=inputs=2:dropout_transition=0",
        "-t", str(TARGET_DURATION),
        temp_audio
    ])

    os.replace(temp_audio, FINAL_AUDIO)
    return TARGET_DURATION

# ================= VIDEO =================
def create_video(duration):
    """Create video from images + final audio"""
    print("🎞 Creating video...")
    run([
        "ffmpeg", "-y",
        "-framerate", "1/6",  # 1 image per 6 seconds → ~10 min
        "-pattern_type", "glob",
        "-i", f"{IMAGE_DIR}/*.jpg",
        "-i", FINAL_AUDIO,
        "-t", str(duration),
        "-vf", "scale=1280:720,format=yuv420p",
        "-c:v", "libx264",
        "-preset", "slow",
        "-c:a", "aac",
        "-b:a", "192k",
        FINAL_VIDEO
    ])

# ================= YOUTUBE UPLOAD =================
def upload_youtube():
    """Upload video to YouTube"""
    print("📤 Uploading to YouTube...")
    token_info = json.loads(
        base64.b64decode(os.environ["YOUTUBE_TOKEN_BASE64"]).decode()
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
                    "यह एक दिव्य कथा श्रृंखला है।\n\n"
                    "🙏 चैनल को Subscribe करें\n"
                    "🔔 Like और Share करें\n"
                ),
                "categoryId": "22"
            },
            "status": {"privacyStatus": "public"}
        },
        media_body=MediaFileUpload(FINAL_VIDEO, mimetype="video/mp4", resumable=True)
    )

    response = request.execute()
    print("✅ Uploaded. Video ID:", response["id"])

# ================= MAIN =================
def main():
    download_images(count=50)
    generate_narration()
    duration = mix_tanpura()
    create_video(duration)
    upload_youtube()

if __name__ == "__main__":
    main()