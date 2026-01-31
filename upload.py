import os
import subprocess
import requests
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# ---------------- CONFIG ----------------
SCRIPT_FILE = "script.txt"
IMAGE_DIR = "images"
AUDIO_DIR = "audio_blocks"
VIDEO_DIR = "video_blocks"
FINAL_VIDEO = "final_video.mp4"

PIXABAY_API_KEY = os.environ.get("PIXABAY_API_KEY")

os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)

# ---------------- UTILS ----------------
def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)

# ---------------- PLACEHOLDER IMAGE ----------------
def create_placeholder(path, text):
    img = Image.new("RGB", (1280, 720), (20, 12, 6))
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 42)
    except:
        font = ImageFont.load_default()
    d.text((60, 330), text[:120], fill=(255, 200, 80), font=font)
    img.save(path)

# ---------------- IMAGES (PIXABAY) ----------------
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
            "per_page": 50,
        },
        timeout=30
    ).json()

    hits = r.get("hits", [])

    for i, text in enumerate(blocks):
        img_path = f"{IMAGE_DIR}/{i:03d}.jpg"

        if hits:
            try:
                url = hits[i % len(hits)]["largeImageURL"]
                img = requests.get(url, timeout=30).content
                with open(img_path, "wb") as f:
                    f.write(img)
            except Exception:
                print(f"⚠ Image failed for block {i}, using placeholder")
                create_placeholder(img_path, text)
        else:
            print(f"⚠ No images found, using placeholder for block {i}")
            create_placeholder(img_path, text)

# ---------------- AUDIO (HINDI – NEURAL) ----------------
def generate_audio(blocks):
    print("🎙 Generating NATURAL Hindi voice (Azure Neural)...")

    for i, text in enumerate(blocks):
        if not text.strip():
            continue

        out = f"{AUDIO_DIR}/{i:03d}.wav"

        run([
            "python", "-m", "edge_tts",
            "--voice", "hi-IN-MadhurNeural",
            "--rate", "+0%",
            "--pitch", "+0Hz",
            "--text", text,
            "--write-media", out
        ])

# ---------------- VIDEO ----------------
def create_video(blocks):
    print("🎞 Creating video blocks...")
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
        "-f", "concat",
        "-safe", "0",
        "-i", "list.txt",
        "-c", "copy",
        FINAL_VIDEO
    ])

# ---------------- MAIN ----------------
def main():
    blocks = Path(SCRIPT_FILE).read_text(encoding="utf-8").split("\n\n")

    download_images(blocks)
    generate_audio(blocks)
    create_video(blocks)

    print("✅ FINAL VIDEO READY:", FINAL_VIDEO)

if __name__ == "__main__":
    main()