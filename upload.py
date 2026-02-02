import os
import requests
import asyncio
from pathlib import Path
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
import subprocess
import edge_tts
import random
import time
import json

# ---------------- CONFIG ----------------
CHANNEL_NAME = "Sanatan Gyan Dhara"
IMAGE_DIR = "images"
AUDIO_DIR = "audio_blocks"
VIDEO_DIR = "video_blocks"
FINAL_VIDEO = "final_video.mp4"
TANPURA_FILE = "audio/tanpura.mp3"  # you already have this
FRONT_COVER = f"{IMAGE_DIR}/front_cover.jpg"
SCRIPT_FILE = "script.txt"
BLOCKS = 5  # number of video blocks

os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)

# ---------------- UTILS ----------------
def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)

def placeholder(path, text="ॐ नमो नारायणाय"):
    img = Image.new("RGB", (1280, 720), (10, 5, 0))
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 48)
    except:
        font = None
    d.text((60, 330), text, fill=(255, 215, 0), font=font)
    img.save(path)

# ---------------- AUDIO GENERATION ----------------
async def generate_audio(text, index):
    out = f"{AUDIO_DIR}/{index:03d}.mp3"
    communicate = edge_tts.Communicate(text=text, voice="hi-IN-MadhurNeural")
    await communicate.save(out)

def generate_audio_blocks(blocks):
    async def runner():
        for i, text in enumerate(blocks):
            if text.strip():
                await generate_audio(text, i)
    asyncio.run(runner())

# ---------------- IMAGE FETCH ----------------
def fetch_pixabay_images(query, count):
    PIXABAY_API_KEY = os.environ.get("PIXABAY_API_KEY")
    if not PIXABAY_API_KEY:
        print("❌ PIXABAY_API_KEY not set, using placeholders")
        return [placeholder_path(f"{IMAGE_DIR}/{i:03d}.jpg") for i in range(count)]
    url = f"https://pixabay.com/api/?key={PIXABAY_API_KEY}&q={query}&image_type=photo&per_page={count}"
    try:
        res = requests.get(url, timeout=15).json()
        hits = res.get("hits", [])
        paths = []
        for i, img in enumerate(hits[:count]):
            img_url = img.get("largeImageURL")
            path = f"{IMAGE_DIR}/{i:03d}.jpg"
            try:
                r = requests.get(img_url, timeout=15)
                if r.status_code == 200:
                    with open(path, "wb") as f:
                        f.write(r.content)
                    paths.append(path)
            except:
                placeholder(path)
                paths.append(path)
        return paths
    except Exception as e:
        print("⚠ Failed to fetch Pixabay images:", e)
        return [placeholder_path(f"{IMAGE_DIR}/{i:03d}.jpg") for i in range(count)]

# ---------------- VIDEO CREATION ----------------
def make_video_block(image_file, audio_file, index):
    out = f"{VIDEO_DIR}/{index:03d}.mp4"
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", image_file,
        "-i", audio_file,
        "-i", TANPURA_FILE,
        "-filter_complex",
        "[2:a]volume=0.2[a2];[1:a][a2]amix=inputs=2:duration=first[a];"
        "[0:v]scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720,setsar=1[v]",
        "-map", "[v]",
        "-map", "[a]",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-shortest",
        out
    ]
    run(cmd)
    return out

def concat_videos(clips, output_file):
    with open("list.txt", "w") as f:
        for c in clips:
            f.write(f"file '{c}'\n")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "list.txt", "-c", "copy", output_file])

# ---------------- MAIN ----------------
def main():
    print("🚀 Starting Sanatan Gyan Dhara bot")

    # ---------------- SCRIPT ----------------
    if not os.path.exists(SCRIPT_FILE):
        raise Exception(f"{SCRIPT_FILE} not found!")
    with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
        script_text = f.read()

    # ---------------- IMAGES ----------------
    images = []
    # Front cover always Vishnu image from Pixabay
    front = fetch_pixabay_images("lord vishnu", 1)
    if front:
        images.append(front[0])
    else:
        placeholder(FRONT_COVER, "Vishnu")
        images.append(FRONT_COVER)

    # Additional images for the video blocks
    additional_images = fetch_pixabay_images("krishna vishnu", BLOCKS-1)
    images.extend(additional_images)

    # ---------------- AUDIO ----------------
    print("🔊 Generating narration...")
    # Add intro and outro
    intro_text = f"नमस्कार। स्वागत है आप सभी का {CHANNEL_NAME} श्रृंखला में।"
    outro_text = "🙏 अगर आपको यह वीडियो पसंद आया हो, तो कृपया लाइक, शेयर और सब्सक्राइब जरूर करें।"
    blocks_text = [intro_text] + [script_text] + [outro_text]
    generate_audio_blocks(blocks_text)

    # ---------------- VIDEO BLOCKS ----------------
    print("🎞 Creating devotional video blocks...")
    video_clips = []
    for i, img in enumerate(images):
        audio_file = f"{AUDIO_DIR}/{i:03d}.mp3"
        clip = make_video_block(img, audio_file, i)
        video_clips.append(clip)

    # ---------------- CONCATENATE ----------------
    print("🔗 Concatenating video blocks...")
    concat_videos(video_clips, FINAL_VIDEO)
    print("✅ FINAL VIDEO READY:", FINAL_VIDEO)

if __name__ == "__main__":
    main()