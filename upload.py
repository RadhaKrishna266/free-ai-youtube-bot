import os
import subprocess
import requests
import asyncio
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import edge_tts
import sys
import time

# ---------------- CONFIG ----------------
SCRIPT_FILE = "script.txt"
IMAGE_DIR = "images"
AUDIO_DIR = "audio_blocks"
VIDEO_DIR = "video_blocks"
FINAL_VIDEO = "final_video.mp4"
TANPURA_FILE = "audio/tanpura.mp3"

MAX_IMAGES = 10
IMAGE_SIZE = (1280, 720)

HEADERS = {
    "User-Agent": "SanatanGyanDharaBot/1.0 (contact: sanatan@example.com)",
    "Accept": "application/json"
}

VISHNU_CATEGORIES = [
    "Vishnu",
    "Lakshmi_Narayana",
    "Ananta_Shesh",
    "Vaikuntha",
    "Padmanabhaswamy_Temple"
]

# ---------------- SETUP ----------------
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)

def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)

# ---------------- PLACEHOLDER (LAST RESORT) ----------------
def make_vishnu_placeholder(path, text):
    img = Image.new("RGB", IMAGE_SIZE, (10, 5, 0))
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 48)
    except:
        font = None
    d.text((80, 320), text, fill=(255, 215, 0), font=font)
    img.save(path)

# ---------------- WIKIMEDIA CATEGORY FETCH ----------------
def fetch_category_images(category, limit=5):
    url = "https://commons.wikimedia.org/w/api.php"
    params = {
        "action": "query",
        "list": "categorymembers",
        "cmtitle": f"Category:{category}",
        "cmtype": "file",
        "cmlimit": limit,
        "format": "json",
        "origin": "*"
    }

    images = []

    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=20)
        r.raise_for_status()
        data = r.json()

        for item in data.get("query", {}).get("categorymembers", []):
            title = item["title"]
            info = requests.get(
                "https://commons.wikimedia.org/w/api.php",
                headers=HEADERS,
                params={
                    "action": "query",
                    "titles": title,
                    "prop": "imageinfo",
                    "iiprop": "url|size",
                    "format": "json",
                    "origin": "*"
                },
                timeout=20
            ).json()

            pages = info.get("query", {}).get("pages", {})
            for p in pages.values():
                img = p.get("imageinfo", [{}])[0]
                if img.get("width", 0) >= 1000:
                    images.append(img["url"])

    except Exception as e:
        print(f"⚠ Wikimedia category error ({category}):", e)

    return images

# ---------------- IMAGE COLLECTION ----------------
def collect_vishnu_images():
    collected = []

    for cat in VISHNU_CATEGORIES:
        if len(collected) >= MAX_IMAGES:
            break
        imgs = fetch_category_images(cat, limit=6)
        for img in imgs:
            if img not in collected:
                collected.append(img)
            if len(collected) >= MAX_IMAGES:
                break
        time.sleep(1)  # polite delay

    return collected

# ---------------- DOWNLOAD & PROCESS ----------------
def prepare_images(urls, count):
    paths = []

    if not urls:
        print("⚠ No Wikimedia images. Creating Vishnu placeholders...")
        for i in range(count):
            path = f"{IMAGE_DIR}/{i:03d}.jpg"
            make_vishnu_placeholder(path, "ॐ नमो नारायणाय")
            paths.append(path)
        return paths

    for i in range(count):
        path = f"{IMAGE_DIR}/{i:03d}.jpg"
        url = urls[i % len(urls)]

        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            with open(path, "wb") as f:
                f.write(r.content)
            img = Image.open(path).convert("RGB")
            img.thumbnail(IMAGE_SIZE, Image.Resampling.LANCZOS)
            img.save(path)
        except:
            make_vishnu_placeholder(path, "ॐ नमो नारायणाय")

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
        img = images[i]
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

    blocks.insert(0, "नमस्कार। आइए भगवान विष्णु के दिव्य स्वरूप का ध्यान करें।")
    blocks.append("🙏 वीडियो पसंद आए तो Sanatan Gyan Dhara को सब्सक्राइब करें।")

    print("🌐 Collecting authentic Vishnu images automatically...")
    urls = collect_vishnu_images()

    print(f"🖼 Images found: {len(urls)}")
    images = prepare_images(urls, len(blocks))

    print("🔊 Generating audio...")
    generate_audio(blocks)

    print("🎬 Creating video...")
    create_video(images, len(blocks))

    print("✅ FINAL VIDEO READY:", FINAL_VIDEO)

if __name__ == "__main__":
    main()