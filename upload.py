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

MAX_IMAGES = 8

VISHNU_TERMS = [
    "Vishnu",
    "Vaikuntha Vishnu",
    "Ananta Shayana Vishnu",
    "Lakshmi Narayan",
    "Padmanabhaswamy Vishnu",
    "Chaturbhuja Vishnu"
]

# ---------------- CREATE FOLDERS ----------------
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)

# ---------------- UTILS ----------------
def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)

# ---------------- WIKIMEDIA API (PROPER WAY) ----------------
def fetch_wikimedia_images(search, limit=3):
    url = "https://commons.wikimedia.org/w/api.php"
    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": search,
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
    except:
        pass

    return images

# ---------------- COLLECT VISHNU IMAGES ----------------
def collect_vishnu_images():
    images = []

    for term in VISHNU_TERMS:
        if len(images) >= MAX_IMAGES:
            break
        imgs = fetch_wikimedia_images(term, limit=4)
        for img in imgs:
            if img not in images:
                images.append(img)
            if len(images) >= MAX_IMAGES:
                break

    if not images:
        print("❌ No Vishnu images found automatically")
        sys.exit(1)

    return images

# ---------------- DOWNLOAD & PROCESS ----------------
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
    voice = edge_tts.Communicate(text=text, voice="hi-IN-MadhurNeural")
    await voice.save(out)

def generate_audio(blocks):
    async def runner():
        for i, t in enumerate(blocks):
            await gen_audio(t, i)
    asyncio.run(runner())

# ---------------- VIDEO ----------------
def create_video(images, blocks_count):
    clips = []

    for i in range(blocks_count):
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
        "नमस्कार। स्वागत है आप सभी का Sanatan Gyan Dhara चैनल पर। "
        "आज हम भगवान विष्णु के दिव्य स्वरूप का स्मरण करेंगे।"
    )
    blocks.append(
        "🙏 वीडियो पसंद आए तो लाइक, शेयर और सब्सक्राइब अवश्य करें। "
        "Sanatan Gyan Dhara — सनातन ज्ञान की धारा।"
    )

    print("🌐 Collecting authentic Vishnu images automatically...")
    image_urls = collect_vishnu_images()
    images = prepare_images(image_urls)

    print(f"🖼 Vishnu images collected: {len(images)}")
    print(f"📜 Script blocks: {len(blocks)}")

    generate_audio(blocks)
    create_video(images, len(blocks))

    print("✅ FINAL VIDEO READY:", FINAL_VIDEO)

if __name__ == "__main__":
    main()