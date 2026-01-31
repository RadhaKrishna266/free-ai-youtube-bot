import os
import subprocess
import requests
from pathlib import Path
from TTS.api import TTS
from PIL import Image, ImageDraw, ImageFont

# ================= CONFIG =================
SCRIPT_FILE = "script.txt"
IMAGE_DIR = "images"
AUDIO_DIR = "audio_blocks"
VIDEO_DIR = "video_blocks"
FINAL_VIDEO = "final_video.mp4"

PIXABAY_API_KEY = os.environ.get("PIXABAY_API_KEY")

os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)

# ================= UTILS =================
def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)

# ================= FALLBACK IMAGE =================
def create_placeholder(path, text):
    img = Image.new("RGB", (1280, 720), color=(20, 20, 20))
    d = ImageDraw.Draw(img)
    msg = text[:80] + "..." if len(text) > 80 else text
    d.text((60, 330), msg, fill=(255, 215, 0))
    img.save(path)

# ================= IMAGES =================
def download_images(blocks):
    print("🖼 Downloading images from Pixabay...")
    query = "Lord Vishnu Krishna Hindu devotional art"

    r = requests.get(
        "https://pixabay.com/api/",
        params={
            "key": PIXABAY_API_KEY,
            "q": query,
            "image_type": "photo",
            "orientation": "horizontal",
            "safesearch": "true",
            "per_page": 50
        }
    ).json()

    hits = r.get("hits", [])

    for i, text in enumerate(blocks):
        img_path = f"{IMAGE_DIR}/{i:03d}.jpg"

        if hits:
            img_url = hits[i % len(hits)]["largeImageURL"]
            img = requests.get(img_url).content
            with open(img_path, "wb") as f:
                f.write(img)
        else:
            print(f"⚠ No image found for block {i}, using placeholder")
            create_placeholder(img_path, text)

# ================= AUDIO (XTTS – SAFE MODE) =================
def generate_audio(blocks):
    print("🎙 Generating Hindi audio with XTTS (SAFE MODE)...")

    tts = TTS(
        model_name="tts_models/multilingual/multi-dataset/xtts_v2",
        gpu=False
    )

    for i, text in enumerate(blocks):
        out = f"{AUDIO_DIR}/{i:03d}.wav"
        if not text.strip():
            continue

        tts.tts_to_file(
            text=text,
            file_path=out,
            language="hi"
        )

# ================= VIDEO =================
def create_video(blocks):
    print("🎞 Creating video blocks...")
    clips = []

    for i in range(len(blocks)):
        audio = f"{AUDIO_DIR}/{i:03d}.wav"
        image = f"{IMAGE_DIR}/{i:03d}.jpg"
        clip = f"{VIDEO_DIR}/{i:03d}.mp4"

        run([
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", image,
            "-i", audio,
            "-vf", "scale=1280:720,format=yuv420p",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-shortest",
            clip
        ])
        clips.append(clip)

    with open("list.txt", "w") as f:
        for c in clips:
            f.write(f"file '{c}'\n")

    run([
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", "list.txt",
        "-c", "copy",
        FINAL_VIDEO
    ])

# ================= MAIN =================
def main():
    blocks = Path(SCRIPT_FILE).read_text(encoding="utf-8").split("\n\n")

    download_images(blocks)
    generate_audio(blocks)
    create_video(blocks)

    print("✅ FINAL VIDEO READY:", FINAL_VIDEO)

if __name__ == "__main__":
    main()