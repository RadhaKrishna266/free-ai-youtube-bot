import os
import requests
import asyncio
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import edge_tts
import subprocess
import random

# ---------------- CONFIG ----------------
SCRIPT_FILE = "script.txt"
IMAGE_DIR = "images"
AUDIO_DIR = "audio_blocks"
VIDEO_DIR = "video_blocks"
FINAL_VIDEO = "final_video.mp4"
TANPURA_FILE = "audio/tanpura.mp3"
HF_API_KEY = os.environ.get("HF_API_KEY")

# Google image search URL you provided
GOOGLE_IMAGE_URL = "https://www.google.com/search?q=vaikunth+vishnu+vishnu+avtara+lakshmi+vishnh+animated+wallpapers+only+photos+without+text&tbm=isch"

# ---------------- CREATE FOLDERS ----------------
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)

# ---------------- UTILS ----------------
def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)

# ---------------- IMAGE SCRAPER ----------------
def fetch_google_images(url, n):
    print("🌐 Fetching images from Google...")
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "lxml")
    imgs = soup.find_all("img")
    urls = []
    for img in imgs:
        src = img.get("src")
        if src and src.startswith("http"):
            urls.append(src)
    # Randomize and pick first n unique images
    urls = list(dict.fromkeys(urls))
    if len(urls) < n:
        print(f"⚠ Only found {len(urls)} images, will reuse some.")
    return urls

def download_images(blocks):
    urls = fetch_google_images(GOOGLE_IMAGE_URL, len(blocks))
    for i, text in enumerate(blocks):
        img_path = f"{IMAGE_DIR}/{i:03d}.jpg"
        try:
            img_url = urls[i % len(urls)]
            r = requests.get(img_url, timeout=20)
            with open(img_path, "wb") as f:
                f.write(r.content)
        except Exception as e:
            print("❌ Image download failed, using fallback black image.", e)
            from PIL import Image, ImageDraw
            img = Image.new("RGB", (1280, 720), (0, 0, 0))
            d = ImageDraw.Draw(img)
            d.text((50, 330), text[:50], fill=(255, 255, 255))
            img.save(img_path)

# ---------------- AUDIO GENERATION ----------------
async def generate_single_audio(text, index):
    out = f"{AUDIO_DIR}/{index:03d}.mp3"
    communicate = edge_tts.Communicate(text=text, voice="hi-IN-MadhurNeural")
    await communicate.save(out)

def generate_audio(blocks):
    async def runner():
        for i, text in enumerate(blocks):
            if text.strip():
                await generate_single_audio(text, i)
    asyncio.run(runner())

# ---------------- VIDEO CREATION ----------------
def create_video(blocks):
    clips = []
    for i in range(len(blocks)):
        img = f"{IMAGE_DIR}/{i:03d}.jpg"
        aud = f"{AUDIO_DIR}/{i:03d}.mp3"
        clip = f"{VIDEO_DIR}/{i:03d}.mp4"
        run([
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", img,
            "-i", aud,
            "-i", TANPURA_FILE,
            "-filter_complex",
            "[2:a]volume=0.2[a2];[1:a][a2]amix=inputs=2:duration=first:dropout_transition=2[a]",
            "-map", "0:v",
            "-map", "[a]",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-shortest",
            clip
        ])
        clips.append(clip)

    # Concatenate all clips
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
    intro = "नमस्कार। स्वागत है आप सभी का VishnuPriya श्रृंखला में। आज हम आपके लिए Vishnu Purana का पहला एपिसोड लाए हैं।"
    outro = "\n\n🙏 अगर आपको यह वीडियो पसंद आया हो, तो कृपया लाइक, शेयर और सब्सक्राइब जरूर करें। हर दिन एक नया एपिसोड आएगा।"
    blocks.insert(0, intro)
    blocks.append(outro)

    download_images(blocks)
    generate_audio(blocks)
    create_video(blocks)
    print("✅ FINAL VIDEO READY:", FINAL_VIDEO)

if __name__ == "__main__":
    main()