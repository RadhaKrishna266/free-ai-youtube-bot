import os
import sys
import subprocess
import requests
from pathlib import Path
from PIL import Image, ImageDraw

# ================= AUTO-INSTALL TTS =================
try:
    from TTS.api import TTS
except ModuleNotFoundError:
    print("📦 TTS not found, installing...")
    subprocess.run([sys.executable, "-m", "pip", "install", "TTS==0.22.0"], check=True)
    from TTS.api import TTS

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

# ================= PLACEHOLDER IMAGE =================
def placeholder(path, text):
    img = Image.new("RGB", (1280, 720), (15, 15, 15))
    d = ImageDraw.Draw(img)
    d.text((60, 330), text[:70], fill=(255, 200, 0))
    img.save(path)

# ================= IMAGES =================
def download_images(blocks):
    print("🖼 Downloading images from Pixabay...")

    r = requests.get(
        "https://pixabay.com/api/",
        params={
            "key": PIXABAY_API_KEY,
            "q": "Lord Vishnu Krishna Hindu devotional art",
            "image_type": "photo",
            "orientation": "horizontal",
            "safesearch": "true",
            "per_page": 50
        }
    ).json()

    hits = r.get("hits", [])

    for i, text in enumerate(blocks):
        path = f"{IMAGE_DIR}/{i:03d}.jpg"
        if hits:
            img_url = hits[i % len(hits)]["largeImageURL"]
            img = requests.get(img_url).content
            open(path, "wb").write(img)
        else:
            print(f"⚠ Placeholder used for block {i}")
            placeholder(path, text)

# ================= AUDIO (HINDI XTTS) =================
def generate_audio(blocks):
    print("🎙 Generating pure Hindi narration...")

    tts = TTS(
        model_name="tts_models/multilingual/multi-dataset/xtts_v2",
        gpu=False
    )

    for i, text in enumerate(blocks):
        if not text.strip():
            continue
        tts.tts_to_file(
            text=text,
            language="hi",
            file_path=f"{AUDIO_DIR}/{i:03d}.wav"
        )

# ================= VIDEO =================
def create_video(blocks):
    print("🎞 Creating video...")
    clips = []

    for i in range(len(blocks)):
        clip = f"{VIDEO_DIR}/{i:03d}.mp4"
        run([
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", f"{IMAGE_DIR}/{i:03d}.jpg",
            "-i", f"{AUDIO_DIR}/{i:03d}.wav",
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
        "-f", "concat", "-safe", "0",
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