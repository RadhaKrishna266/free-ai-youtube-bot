import os
import requests
import subprocess
from pathlib import Path
import random

# ================= CONFIG =================
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")

WIDTH = 1280
HEIGHT = 720
FPS = 25
IMAGE_DURATION = 6
TOTAL_IMAGES = 10

BASE = Path(".")
IMG_DIR = BASE / "images"
VID_DIR = BASE / "video_blocks"
AUD_DIR = BASE / "audio"

IMG_DIR.mkdir(exist_ok=True)
VID_DIR.mkdir(exist_ok=True)
AUD_DIR.mkdir(exist_ok=True)

# ================= UTILS =================
def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)

# ================= IMAGE FETCH =================
def fetch_images():
    headers = {"Authorization": PEXELS_API_KEY}

    queries = [
        "Vishnu digital art",
        "Vaikuntha Vishnu illustration",
        "Lakshmi Narayan painting",
        "Vishnu avatars artwork",
        "Hindu god Vishnu illustration"
    ]

    urls = []

    for q in queries:
        print(f"🔍 Searching: {q}")
        r = requests.get(
            f"https://api.pexels.com/v1/search?query={q}&per_page=8&orientation=landscape",
            headers=headers,
            timeout=20
        )

        if r.status_code == 200:
            for p in r.json().get("photos", []):
                urls.append(p["src"]["large2x"])

    if not urls:
        raise RuntimeError("❌ No Vishnu images found")

    random.shuffle(urls)
    return urls[:TOTAL_IMAGES]

def download_images(urls):
    paths = []
    for i, u in enumerate(urls):
        p = IMG_DIR / f"{i:03}.jpg"
        p.write_bytes(requests.get(u, timeout=30).content)
        paths.append(p)
    return paths

# ================= AUDIO =================
def create_audio():
    audio = AUD_DIR / "bg.mp3"
    if audio.exists():
        return audio

    print("🎵 Creating background tanpura")
    run([
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "sine=frequency=110:duration=300",
        "-af", "volume=0.25",
        str(audio)
    ])
    return audio

# ================= VIDEO BLOCKS =================
def make_blocks(images, audio):
    blocks = []

    for i, img in enumerate(images):
        out = VID_DIR / f"{i:03}.mp4"

        # SAFE CINEMATIC ZOOM (NO zoompan)
        vf = (
            f"scale={WIDTH*1.1}:{HEIGHT*1.1},"
            f"crop={WIDTH}:{HEIGHT}"
        )

        run([
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(img),
            "-i", str(audio),
            "-vf", vf,
            "-t", str(IMAGE_DURATION),
            "-map", "0:v",
            "-map", "1:a",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-shortest",
            str(out)
        ])

        blocks.append(out)

    return blocks

# ================= FINAL MERGE =================
def concat(blocks):
    lst = BASE / "list.txt"
    with open(lst, "w") as f:
        for b in blocks:
            f.write(f"file '{b.resolve()}'\n")

    run([
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(lst),
        "-c", "copy",
        "final_video.mp4"
    ])

# ================= MAIN =================
def main():
    print("🛕 Fetching Vishnu artwork images...")
    urls = fetch_images()

    print("⬇ Downloading images...")
    images = download_images(urls)

    print("🔊 Preparing audio...")
    audio = create_audio()

    print("🎞 Creating video blocks...")
    blocks = make_blocks(images, audio)

    print("🎬 Merging final video...")
    concat(blocks)

    print("✅ final_video.mp4 READY")

if __name__ == "__main__":
    main()