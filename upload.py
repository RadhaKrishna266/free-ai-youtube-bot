import os
import subprocess
import requests
from pathlib import Path
from PIL import Image, ImageDraw

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
def placeholder(path, text):
    img = Image.new("RGB", (1280, 720), (15, 10, 5))
    d = ImageDraw.Draw(img)
    d.text((40, 340), text[:80], fill=(255, 200, 0))
    img.save(path)

# ---------------- IMAGES (PIXABAY ONLY) ----------------
def download_images(blocks):
    print("🖼 Downloading devotional images...")

    hits = []
    if PIXABAY_API_KEY:
        r = requests.get(
            "https://pixabay.com/api/",
            params={
                "key": PIXABAY_API_KEY,
                "q": "Lord Vishnu Krishna Hindu devotional art",
                "image_type": "photo",
                "orientation": "horizontal",
                "safesearch": "true",
                "per_page": 50
            },
            timeout=30
        ).json()
        hits = r.get("hits", [])

    for i, text in enumerate(blocks):
        path = f"{IMAGE_DIR}/{i:03d}.jpg"
        if hits:
            img = requests.get(hits[i % len(hits)]["largeImageURL"], timeout=30).content
            with open(path, "wb") as f:
                f.write(img)
        else:
            placeholder(path, text)

# ---------------- HINDI AUDIO (REAL, CI-SAFE) ----------------
def generate_audio(blocks):
    print("🎙 Generating REAL Hindi voice (espeak)...")

    for i, text in enumerate(blocks):
        out = f"{AUDIO_DIR}/{i:03d}.wav"

        if not text.strip():
            # silent filler so ffmpeg never breaks
            run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc", "-t", "1", out])
            continue

        run([
            "espeak",
            "-v", "hi",
            "-s", "135",
            "-w", out,
            text
        ])

# ---------------- VIDEO ----------------
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