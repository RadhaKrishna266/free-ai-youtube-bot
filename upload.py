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

# Optional OpenAI for front cover
try:
    import openai
except:
    openai = None

# ---------------- CONFIG ----------------
CHANNEL_NAME = "Sanatan Gyan Dhara"
IMAGE_DIR = "images"
AUDIO_DIR = "audio_blocks"
VIDEO_DIR = "video_blocks"
FINAL_VIDEO = "final_video.mp4"
TANPURA_FILE = "audio/tanpura.mp3"
FRONT_COVER = f"{IMAGE_DIR}/0.jpg"
BLOCKS = 5  # number of video blocks
SCRIPT_FILE = "script.txt"  # narration script

# ---------------- CREATE FOLDERS ----------------
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs("audio", exist_ok=True)

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

# ---------------- TANPURA GENERATION ----------------
def generate_tanpura(duration=180):
    if not os.path.exists(TANPURA_FILE):
        run([
            "ffmpeg", "-y", "-f", "lavfi",
            f"-i", f"sine=frequency=110:duration={duration}",
            "-af", "volume=0.18",
            TANPURA_FILE
        ])

# ---------------- IMAGE FETCH ----------------
def fetch_wallpapers(query, count):
    """
    Scrapes wallpapers from Bhagwan Puja
    """
    base_url = "https://www.bhagwanpuja.com/wallpapers/"
    try:
        res = requests.get(base_url, timeout=15)
        soup = BeautifulSoup(res.text, "lxml")
        imgs = [img["src"] for img in soup.find_all("img") if query.lower() in img.get("alt", "").lower()]
        paths = []
        for i, url in enumerate(imgs[:count]):
            path = f"{IMAGE_DIR}/{i+1:03d}.jpg"  # start from 1 since 0 is front cover
            try:
                r = requests.get(url, timeout=15)
                if r.status_code == 200:
                    with open(path, "wb") as f:
                        f.write(r.content)
                    paths.append(path)
                else:
                    placeholder(path)
                    paths.append(path)
            except:
                placeholder(path)
                paths.append(path)
        return paths
    except Exception as e:
        print("⚠ Failed to fetch images:", e)
        paths = []
        for i in range(count):
            path = f"{IMAGE_DIR}/{i+1:03d}.jpg"
            placeholder(path)
            paths.append(path)
        return paths

# ---------------- FRONT COVER ----------------
def generate_front_cover():
    if os.path.exists(FRONT_COVER):
        print("✅ Using existing front cover")
        return FRONT_COVER

    if openai and os.getenv("OPENAI_API_KEY"):
        try:
            print("🌟 Generating front cover via OpenAI...")
            prompt = "Vishnu Purana book front cover, divine Hindu style, vibrant, highly detailed, 1280x720"
            openai.api_key = os.getenv("OPENAI_API_KEY")
            resp = openai.Image.create(prompt=prompt, n=1, size="1280x720")
            img_url = resp["data"][0]["url"]
            r = requests.get(img_url, timeout=20)
            if r.status_code == 200:
                with open(FRONT_COVER, "wb") as f:
                    f.write(r.content)
                return FRONT_COVER
        except Exception as e:
            print("⚠ Failed to generate front cover:", e)
    
    print("⚠ Using placeholder for front cover")
    placeholder(FRONT_COVER, text="Vishnu Purana")
    return FRONT_COVER

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
        "[0:v]scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720,zoompan=z='min(zoom+0.0005,1.06)':d=150:fps=25[v]",
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
        raise Exception("❌ script.txt not found!")
    with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
        script_lines = [line.strip() for line in f if line.strip()]

    # ---------------- IMAGES ----------------
    images = [generate_front_cover()]
    images += fetch_wallpapers("vishnu", BLOCKS-1)

    # ---------------- AUDIO ----------------
    print("🔊 Generating narration...")
    generate_audio_blocks(script_lines)

    # ---------------- TANPURA ----------------
    generate_tanpura(duration=300)

    # ---------------- VIDEO BLOCKS ----------------
    print("🎞 Creating devotional video blocks...")
    video_clips = []
    for i, img in enumerate(images):
        audio_file = f"{AUDIO_DIR}/{i:03d}.mp3" if i < len(script_lines) else TANPURA_FILE
        clip = make_video_block(img, audio_file, i)
        video_clips.append(clip)

    # ---------------- CONCATENATE ----------------
    print("🔗 Concatenating video blocks...")
    concat_videos(video_clips, FINAL_VIDEO)
    print("✅ FINAL VIDEO READY:", FINAL_VIDEO)

if __name__ == "__main__":
    main()