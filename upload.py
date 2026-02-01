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

    # 🎨 ART / ANIMATED STYLE QUERIES
    queries = [
        "Vaikuntha Vishnu digital art",
        "Vishnu illustration Hindu god",
        "Lakshmi Narayan digital painting",
        "Vishnu avatars illustration",
        "Hindu god Vishnu artwork",
        "Krishna Vishnu avatar illustration",
        "Rama Vishnu avatar painting"
    ]

    urls = []

    for q in queries:
        print(f"🔍 Searching: {q}")
        url = f"https://api.pexels.com/v1/search?query={q}&per_page=6&orientation=landscape"
        r = requests.get(url, headers=headers, timeout=20)

        if r.status_code == 200:
            photos = r.json().get("photos", [])
            for p in photos:
                urls.append(p["src"]["large2x"])

    if not urls:
        raise RuntimeError("❌ No animated / art Vishnu images found")

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

    print("🎵 Creating background tanpura tone")
    run([
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "sine=frequency=110:duration=180",
        "-af", "volume=0.18",
        str(audio)
    ])
    return audio

# ================= VIDEO BLOCKS =================
def make_blocks(images, audio):
    blocks = []
    frames = IMAGE_DURATION * FPS

    for i, img in enumerate(images):
        out = VID_DIR / f"{i:03}.mp4"

        filter_complex = (
            # background blur (fills screen)
            f"[0:v]scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
            f"crop={WIDTH}:{HEIGHT},boxblur=25:1[bg];"
            # foreground (NO CROP)
            f"[0:v]scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=decrease,"
            f"pad={WIDTH}:{HEIGHT}:(ow-iw)/2:(oh-ih)/2,"
            f"zoompan=z='min(zoom+0.0005,1.06)':d={frames}:fps={FPS}[fg];"
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2"
        )

        run([
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(img),
            "-i", str(audio),
            "-filter_complex", filter_complex,
            "-map", "0:v",
            "-map", "1:a",
            "-t", str(IMAGE_DURATION),
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
    print("🛕 Fetching animated / art style Vishnu images...")
    urls = fetch_images()

    print("⬇ Downloading images...")
    images = download_images(urls)

    print("🔊 Preparing audio...")
    audio = create_audio()

    print("🎞 Creating devotional video...")
    blocks = make_blocks(images, audio)

    print("🎬 Merging final video...")
    concat(blocks)

    print("✅ final_video.mp4 CREATED SUCCESSFULLY")

if __name__ == "__main__":
    main()