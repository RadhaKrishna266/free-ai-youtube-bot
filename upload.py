import os
import subprocess
import requests
import asyncio
from pathlib import Path
from PIL import Image
import edge_tts
import sys

# ---------------- CONFIG ----------------
SCRIPT_FILE = "script.txt"
IMAGE_DIR = "images"
AUDIO_DIR = "audio_blocks"
VIDEO_DIR = "video_blocks"
FINAL_VIDEO = "final_video.mp4"
TANPURA_FILE = "audio/tanpura.mp3"

MAX_IMAGES = 10

VISHNU_TERMS = [
    "Vishnu",
    "Vaikuntha Vishnu",
    "Ananta Shayana Vishnu",
    "Lakshmi Narayan",
    "Padmanabhaswamy Vishnu"
]

# ---------------- SETUP ----------------
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)

def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)

# ---------------- WIKIMEDIA (CORRECT WAY) ----------------
def fetch_vishnu_images(term, limit=5):
    url = "https://commons.wikimedia.org/w/api.php"
    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": f"intitle:{term}",
        "gsrnamespace": 6,              # 🔑 FILE namespace
        "gsrlimit": limit,
        "prop": "imageinfo",
        "iiprop": "url|size",
        "iiurlwidth": 1920,
        "format": "json"
    }

    images = []

    try:
        r = requests.get(url, params=params, timeout=20).json()
        pages = r.get("query", {}).get("pages", {})
        for p in pages.values():
            info = p.get("imageinfo", [{}])[0]
            if info.get("width", 0) >= 1000:
                images.append(info["url"])
    except Exception as e:
        print("⚠ Wikimedia error:", e)

    return images

# ---------------- IMAGE COLLECTION ----------------
def collect_images():
    collected = []

    for term in VISHNU_TERMS:
        if len(collected) >= MAX_IMAGES:
            break
        imgs = fetch_vishnu_images(term, limit=6)
        for img in imgs:
            if img not in collected:
                collected.append(img)
            if len(collected) >= MAX_IMAGES:
                break

    if not collected:
        print("❌ Wikimedia returned 0 Vishnu images")
        sys.exit(1)

    return collected

# ---------------- DOWNLOAD & PREP ----------------
def prepare_images(urls):
    paths = []
    for i, url in enumerate(urls):
        path = f"{IMAGE_DIR}/{i:03d}.jpg"
        r = requests.get(url, timeout=20)
        with open(path, "wb") as f:
            f.write(r.content)

        img = Image.open(path).convert("RGB")
        img.thumbnail((1280, 720), Image.Resampling.LANCZOS)
        img.save(path)
        paths.append(path)
    return paths

# ---------------- AUDIO ----------------
async def gen_audio(text, idx):
    out = f"{AUDIO_DIR}/{idx:03d}.mp3"
    tts = edge_tts.Communicate(text=text, voice="hi-IN-MadhurNeural")
    await tts.save(out)

def generate_audio(blocks):
    async def runner():
        for i, t in enumerate(blocks):
            await gen_audio(t, i)
    asyncio.run(runner())

# ---------------- VIDEO ----------------
def create_video(images, count):
    clips = []

    for i in range(count):
        img = images[i % len(images)]
        aud = f"{AUDIO_DIR}/{i:03d}.mp3"
        clip = f"{VIDEO_DIR}/{i:03d}.mp4"

        run([
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", img,
            "-i", aud,
            "-i", TANPURA_FILE,
            "-filter_complex",
            "[2:a]volume=0.2[a2];[1:a][a2]amix=inputs=2:duration=first[a]",
            "-map", "0:v",
            "-map", "[a]",
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

    blocks.insert(0,
        "नमस्कार। आज हम भगवान विष्णु के दिव्य स्वरूप का ध्यान करेंगे।"
    )
    blocks.append(
        "🙏 वीडियो पसंद आए तो लाइक और सब्सक्राइब करें।"
    )

    print("🌐 Fetching Vishnu images from Wikimedia...")
    image_urls = collect_images()
    images = prepare_images(image_urls)

    print(f"🖼 Images collected: {len(images)}")
    print("🔊 Generating audio...")
    generate_audio(blocks)

    print("🎬 Creating video...")
    create_video(images, len(blocks))

    print("✅ FINAL VIDEO CREATED:", FINAL_VIDEO)

if __name__ == "__main__":
    main()