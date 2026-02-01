import os
import asyncio
import requests
from pathlib import Path
from bs4 import BeautifulSoup
import edge_tts
import subprocess
from PIL import Image, ImageDraw, ImageFont

# ---------------- CONFIG ----------------
SCRIPT_FILE = "script.txt"
IMAGE_DIR = "images"
AUDIO_DIR = "audio_blocks"
VIDEO_DIR = "video_blocks"
FINAL_VIDEO = "final_video.mp4"
TANPURA_FILE = "audio/tanpura.mp3"  # Must exist
HF_API_KEY = os.environ.get("HF_API_KEY")
GOOGLE_URL = "https://www.google.com/search?q=vaikunth+vishnu+vishnu+avtara+lakshmi+vishnu+animated+wallpapers+only+photos+without+text&tbm=isch"

# ---------------- CREATE FOLDERS ----------------
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)

# ---------------- UTILS ----------------
def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)

def placeholder(path, text="ॐ नमो नारायणाय"):
    """Create fallback black image with text."""
    img = Image.new("RGB", (1280, 720), (0, 0, 0))
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 48)
    except:
        font = None
    d.text((50, 330), text, fill=(255, 255, 0), font=font)
    img.save(path)

# ---------------- GOOGLE IMAGE SCRAPING ----------------
def fetch_google_images(url, max_images=20):
    print("🌐 Fetching images from Google...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")
    img_tags = soup.find_all("img")
    urls = []
    for img in img_tags:
        src = img.get("src")
        if src and src.startswith("http") and src not in urls:
            urls.append(src)
        if len(urls) >= max_images:
            break
    return urls

def download_images(urls):
    paths = []
    for i, url in enumerate(urls):
        out = f"{IMAGE_DIR}/{i:03d}.jpg"
        try:
            r = requests.get(url, timeout=20)
            if r.status_code == 200:
                with open(out, "wb") as f:
                    f.write(r.content)
            else:
                placeholder(out)
        except:
            placeholder(out)
        paths.append(out)
    return paths

# ---------------- AUDIO GENERATION ----------------
async def generate_single_audio(text, index):
    out = f"{AUDIO_DIR}/{index:03d}.mp3"
    communicate = edge_tts.Communicate(
        text=text,
        voice="hi-IN-MadhurNeural"
    )
    await communicate.save(out)

def generate_audio(blocks):
    async def runner():
        for i, text in enumerate(blocks):
            if text.strip():
                await generate_single_audio(text, i)
    asyncio.run(runner())

# ---------------- VIDEO CREATION ----------------
def create_video(blocks, images):
    clips = []
    for i in range(len(blocks)):
        img = images[i % len(images)]
        aud = f"{AUDIO_DIR}/{i:03d}.mp3"
        clip = f"{VIDEO_DIR}/{i:03d}.mp4"

        # Fallback checks
        if not os.path.isfile(img):
            placeholder(img)
        if not os.path.isfile(aud):
            run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100", "-t", "3", aud])
        if not os.path.isfile(TANPURA_FILE):
            run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100", "-t", "3", TANPURA_FILE])

        try:
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
        except Exception as e:
            print(f"❌ FFmpeg failed for clip {i}: {e}")

    # Concatenate
    if clips:
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
    else:
        print("❌ No clips generated")

# ---------------- MAIN ----------------
def main():
    blocks = Path(SCRIPT_FILE).read_text(encoding="utf-8").split("\n\n")
    intro = "नमस्कार। स्वागत है आप सभी का VishnuPurana श्रृंखला में। आज हम आपके लिए Vishnu Purana का पहला एपिसोड लाए हैं।"
    outro = "\n\n🙏 अगर आपको यह वीडियो पसंद आया हो, तो कृपया लाइक, शेयर और सब्सक्राइब जरूर करें।"
    blocks.insert(0, intro)
    blocks.append(outro)

    urls = fetch_google_images(GOOGLE_URL, max_images=len(blocks))
    images = download_images(urls)

    generate_audio(blocks)
    create_video(blocks, images)
    print("✅ FINAL VIDEO READY:", FINAL_VIDEO)

if __name__ == "__main__":
    main()