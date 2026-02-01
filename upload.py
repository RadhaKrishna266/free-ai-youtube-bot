import os
import requests
import asyncio
import subprocess
from pathlib import Path
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
import edge_tts
import random
import time

# ---------------- CONFIG ----------------
SCRIPT_FILE = "script.txt"
IMAGE_DIR = "images"
AUDIO_DIR = "audio_blocks"
VIDEO_DIR = "video_blocks"
FINAL_VIDEO = "final_video.mp4"
TANPURA_FILE = "audio/tanpura.mp3"
HF_API_KEY = os.environ.get("HF_API_KEY")
GOOGLE_SEARCH_URL = "https://www.google.com/search?q=vaikunth+vishnu+vishnu+avtara+lakshmi+narayan+wallpapers&tbm=isch"

# ---------------- CREATE FOLDERS ----------------
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)

# ---------------- UTILS ----------------
def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)

def validate_image(path):
    try:
        with Image.open(path) as img:
            img.verify()
            if img.width < 400 or img.height < 300:
                return False
        return True
    except:
        return False

def placeholder(path, text="ॐ नमो नारायणाय"):
    img = Image.new("RGB", (1280, 720), (0, 0, 0))
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 48)
    except:
        font = None
    d.text((60, 330), text, fill=(255, 215, 0), font=font)
    img.save(path)

# ---------------- FETCH IMAGES ----------------
def fetch_images_google(n):
    print("🌐 Fetching images from Google...")
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(GOOGLE_SEARCH_URL, headers=headers)
    soup = BeautifulSoup(r.text, "lxml")
    imgs = [img['src'] for img in soup.find_all("img") if 'src' in img.attrs]
    imgs = list(dict.fromkeys(imgs))  # remove duplicates
    downloaded = []

    for i, url in enumerate(imgs):
        if len(downloaded) >= n:
            break
        ext = "jpg"
        out_path = f"{IMAGE_DIR}/{i:03d}.{ext}"
        try:
            img_data = requests.get(url, timeout=10).content
            with open(out_path, "wb") as f:
                f.write(img_data)
            if validate_image(out_path):
                downloaded.append(out_path)
            else:
                print(f"⚠️ Invalid image, skipping {url}")
                placeholder(out_path)
                downloaded.append(out_path)
        except Exception as e:
            print("⚠️ Failed to download image:", e)
            placeholder(out_path)
            downloaded.append(out_path)
        time.sleep(0.5)  # avoid rate limit
    return downloaded

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
def create_video(num_blocks):
    clips = []
    for i in range(num_blocks):
        img_file = f"{IMAGE_DIR}/{i:03d}.jpg"
        audio_file = f"{AUDIO_DIR}/{i:03d}.mp3"
        out_file = f"{VIDEO_DIR}/{i:03d}.mp4"

        # fallback checks
        if not os.path.exists(img_file) or not validate_image(img_file):
            print(f"⚠️ Invalid image {img_file}, using placeholder")
            placeholder(img_file)
        if not os.path.exists(audio_file):
            raise FileNotFoundError(f"❌ Missing audio: {audio_file}")
        if not os.path.exists(TANPURA_FILE):
            raise FileNotFoundError(f"❌ Missing tanpura audio: {TANPURA_FILE}")

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", img_file,
            "-i", audio_file,
            "-i", TANPURA_FILE,
            "-filter_complex",
            "[2:a]volume=0.2[a2];[1:a][a2]amix=inputs=2:duration=first:dropout_transition=2[a]",
            "-map", "0:v",
            "-map", "[a]",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-shortest",
            out_file
        ]
        run(cmd)
        clips.append(out_file)

    # concatenate
    with open("list.txt", "w") as f:
        for c in clips:
            f.write(f"file '{c}'\n")
    run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "list.txt",
        "-c", "copy", FINAL_VIDEO
    ])

# ---------------- MAIN ----------------
def main():
    blocks = Path(SCRIPT_FILE).read_text(encoding="utf-8").split("\n\n")
    intro = "नमस्कार। स्वागत है आप सभी का VishnuPriya श्रृंखला में। आज हम आपके लिए Vishnu Purana का पहला एपिसोड लाए हैं।"
    outro = "\n\n🙏 अगर आपको यह वीडियो पसंद आया हो, तो कृपया लाइक, शेयर और सब्सक्राइब जरूर करें। हर दिन एक नया एपिसोड आएगा।"
    blocks.insert(0, intro)
    blocks.append(outro)

    # Fetch high-res images
    images = fetch_images_google(len(blocks))

    # Generate narration audio
    generate_audio(blocks)

    # Create video
    create_video(len(blocks))

    print("✅ FINAL VIDEO READY:", FINAL_VIDEO)

if __name__ == "__main__":
    main()