import os
import requests
import subprocess
from pathlib import Path
import random
import math

# ================= CONFIG =================
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")
WIDTH = 1280
HEIGHT = 720
FPS = 25
IMAGE_DURATION = 5  # seconds per image
TOTAL_IMAGES = 12

BASE_DIR = Path(".")
IMG_DIR = BASE_DIR / "images"
VID_DIR = BASE_DIR / "video_blocks"

IMG_DIR.mkdir(exist_ok=True)
VID_DIR.mkdir(exist_ok=True)

# ================= HELPERS =================
def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)

# ================= FETCH IMAGES =================
def fetch_vishnu_images():
    headers = {"Authorization": PEXELS_API_KEY}

    queries = [
        "Vishnu Hindu god illustration",
        "Vaikuntha Vishnu art",
        "Lakshmi Narayan divine illustration",
        "Vishnu avatars painting",
        "Krishna Vishnu avatar art",
        "Rama Vishnu avatar illustration",
        "Hindu god Vishnu digital art",
        "Hindu mythology illustration"
    ]

    images = []
    for q in queries:
        url = f"https://api.pexels.com/v1/search?query={q}&per_page=5"
        r = requests.get(url, headers=headers, timeout=20)
        if r.status_code == 200:
            data = r.json()
            for p in data.get("photos", []):
                images.append(p["src"]["large2x"])

    if not images:
        raise RuntimeError("❌ No images fetched from Pexels")

    random.shuffle(images)
    return images[:TOTAL_IMAGES]

def download_images(urls):
    paths = []
    for i, url in enumerate(urls):
        path = IMG_DIR / f"{i:03}.jpg"
        r = requests.get(url, timeout=30)
        path.write_bytes(r.content)
        paths.append(path)
    return paths

# ================= VIDEO CREATION =================
def create_video_blocks(images):
    blocks = []

    frames = IMAGE_DURATION * FPS

    for i, img in enumerate(images):
        out = VID_DIR / f"{i:03}.mp4"

        zoom_filter = (
            f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
            f"crop={WIDTH}:{HEIGHT},"
            f"zoompan=z='if(lte(zoom,1.0),1.0,zoom+0.0008)':"
            f"d={frames}:fps={FPS}"
        )

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(img),
            "-vf", zoom_filter,
            "-t", str(IMAGE_DURATION),
            "-pix_fmt", "yuv420p",
            "-c:v", "libx264",
            str(out)
        ]

        run(cmd)
        blocks.append(out)

    return blocks

def concat_videos(videos):
    list_file = BASE_DIR / "list.txt"
    with open(list_file, "w") as f:
        for v in videos:
            f.write(f"file '{v.resolve()}'\n")

    run([
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(list_file),
        "-c", "copy",
        "final_video.mp4"
    ])

# ================= MAIN =================
def main():
    print("🌸 Fetching Vishnu images from Pexels...")
    urls = fetch_vishnu_images()

    print("⬇ Downloading images...")
    images = download_images(urls)

    print("🎞 Creating zoom videos (FULL SCREEN)...")
    videos = create_video_blocks(images)

    print("🎬 Merging final video...")
    concat_videos(videos)

    print("✅ final_video.mp4 created successfully")

if __name__ == "__main__":
    main()