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
SCRIPT_FILE = "script.txt"   # Your Episode 1 script (blocks separated by double newlines)
IMAGE_DIR = "images"         # Will store downloaded Pixabay images
TANPURA = "audio_fixed/tanpura_fixed.mp3"
FINAL_AUDIO = "final_audio.wav"
FINAL_VIDEO = "final_video.mp4"
YOUTUBE_SCOPE = "https://www.googleapis.com/auth/youtube.upload"

PIXABAY_API_KEY = os.environ.get("PIXABAY_API_KEY")  # Set your Pixabay API key

os.makedirs("audio_blocks", exist_ok=True)
os.makedirs("video_blocks", exist_ok=True)
os.makedirs(IMAGE_DIR, exist_ok=True)

# ================= UTILS =================
def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)

# ================= IMAGES =================
def download_images(blocks):
    print("🖼 Downloading images from Pixabay...")
    for i, block in enumerate(blocks):
        # Take first 5 words from block as keyword
        words = block.strip().split()[:5]
        keyword = " ".join(words) if words else "Vishnu Krishna devotional"
        response = requests.get(
            "https://pixabay.com/api/",
            params={
                "key": PIXABAY_API_KEY,
                "q": keyword,
                "image_type": "photo",
                "orientation": "horizontal",
                "per_page": 3
            }
        ).json()

        hits = response.get("hits", [])
        if hits:
            img_url = hits[0]["largeImageURL"]
            img_data = requests.get(img_url).content
            with open(f"{IMAGE_DIR}/{i:03d}.jpg", "wb") as f:
                f.write(img_data)
        else:
            print(f"⚠ No image found for block {i}, using placeholder")
            open(f"{IMAGE_DIR}/{i:03d}.jpg", "wb").close()

# ================= VOICE =================
def generate_audio_blocks(blocks):
    """Generate Hindi narration for each block using single-speaker TTS"""
    print("🎙 Generating narration in blocks...")
    tts = TTS(model_name="tts_models/hi/vits", gpu=False)

    block_files = []
    for i, block in enumerate(blocks):
        if not block.strip():
            continue
        audio_file = f"audio_blocks/{i:03d}.wav"
        print(f"Generating block {i+1}/{len(blocks)}...")
        tts.tts_to_file(
            text=block.strip(),
            language="hi",
            file_path=audio_file,
            speed=1.0
        )
        block_files.append(audio_file)

    # Concatenate all blocks into final narration
    with open("audio_list.txt", "w") as f:
        for bf in block_files:
            f.write(f"file '{bf}'\n")

    run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", "audio_list.txt",
        "-c", "copy", "narration_raw.wav"
    ])

    # Mix with tanpura if available
    if os.path.exists(TANPURA):
        run([
            "ffmpeg", "-y",
            "-i", "narration_raw.wav",
            "-stream_loop", "-1",
            "-i", TANPURA,
            "-filter_complex", "[1:a]volume=0.12,atrim=0:600[bg];[0:a][bg]amix=inputs=2",
            "-t", "600",
            FINAL_AUDIO
        ])
    else:
        run(["ffmpeg", "-y", "-i", "narration_raw.wav", FINAL_AUDIO])

# ================= VIDEO =================
def create_video(blocks):
    """Create video using one image per block"""
    print("🎞 Creating video block-by-block...")
    input_files = []

    for i, block in enumerate(blocks):
        if not block.strip():
            continue
        audio_file = f"audio_blocks/{i:03d}.wav"
        img_file = f"{IMAGE_DIR}/{i:03d}.jpg"
        if not os.path.exists(img_file):
            print(f"⚠ Image missing for block {i}, using last image")
            img_file = f"{IMAGE_DIR}/{i-1:03d}.jpg" if i>0 else f"{IMAGE_DIR}/000.jpg"

        # Get audio duration
        result = subprocess.run(
            ["ffprobe", "-i", audio_file, "-show_entries", "format=duration",
             "-v", "quiet", "-of", "csv=p=0"], capture_output=True, text=True
        )
        duration = float(result.stdout.strip())

        # Create video segment
        segment_file = f"video_blocks/{i:03d}.mp4"
        run([
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", img_file,
            "-i", audio_file,
            "-c:v", "libx264",
            "-t", str(duration),
            "-vf", "scale=1280:720,format=yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            segment_file
        ])
        input_files.append(segment_file)

    # Concatenate video segments
    with open("video_list.txt", "w") as f:
        for vf in input_files:
            f.write(f"file '{vf}'\n")

    run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", "video_list.txt",
        "-c", "copy",
        FINAL_VIDEO
    ])

# ================= YOUTUBE =================
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
    text_blocks = Path(SCRIPT_FILE).read_text(encoding="utf-8").split("\n\n")
    download_images(text_blocks)
    generate_audio_blocks(text_blocks)
    create_video(text_blocks)
    upload_youtube()

if __name__ == "__main__":
    main()