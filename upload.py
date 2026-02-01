import os
import requests
import asyncio
import subprocess
from pathlib import Path
from bs4 import BeautifulSoup
import edge_tts
from PIL import Image

# ---------------- CONFIG ----------------
SCRIPT_FILE = "script.txt"
IMAGE_DIR = "images"
AUDIO_DIR = "audio_blocks"
VIDEO_DIR = "video_blocks"
FINAL_VIDEO = "final_video.mp4"
TANPURA_FILE = "audio/tanpura.mp3"  # must exist
HF_API_KEY = os.environ.get("HF_API_KEY")

# Google search URL for Vishnu images
GOOGLE_URL = "https://www.google.com/search?q=vaikunth+vishnu+vishnu+avtara+lakshmi+vishnu+animated+wallpapers&tbm=isch"

# ---------------- CREATE FOLDERS ----------------
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)

# ---------------- UTILS ----------------
def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)

def download_image(url, path):
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            with open(path, "wb") as f:
                f.write(r.content)
            return True
    except Exception as e:
        print("❌ Failed to download image:", e)
    return False

def fetch_google_images(url, max_images=50):
    """Fetch high-res image URLs from Google search page."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")
    img_tags = soup.find_all("img")

    urls = []
    seen = set()
    for img in img_tags:
        src = img.get("src")
        if src and src.startswith("http") and src not in seen:
            seen.add(src)
            urls.append(src)
        if len(urls) >= max_images:
            break
    return urls

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
def create_video(num_blocks):
    clips = []
    for i in range(num_blocks):
        img_file = f"{IMAGE_DIR}/{i:03d}.jpg"
        audio_file = f"{AUDIO_DIR}/{i:03d}.mp3"
        out_file = f"{VIDEO_DIR}/{i:03d}.mp4"

        if not os.path.exists(img_file):
            print(f"❌ Image missing: {img_file}")
            Image.new("RGB", (1280, 720), (0,0,0)).save(img_file)

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

    # Concatenate all clips
    with open("list.txt", "w") as f:
        for clip in clips:
            f.write(f"file '{clip}'\n")
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
    # Optional intro/outro
    intro = "नमस्कार। स्वागत है आप सभी का VishnuPriya श्रृंखला में। आज हम आपके लिए Vishnu Purana का पहला एपिसोड लाए हैं।"
    outro = "\n\n🙏 अगर आपको यह वीडियो पसंद आया हो, तो कृपया लाइक, शेयर और सब्सक्राइब जरूर करें।"
    blocks.insert(0, intro)
    blocks.append(outro)

    print("🌐 Fetching images from Google...")
    urls = fetch_google_images(GOOGLE_URL, max_images=len(blocks))
    if len(urls) < len(blocks):
        print("⚠️ Not enough high-res images, repeating allowed with placeholder fallback.")

    print("🖼 Downloading images...")
    used = set()
    for i in range(len(blocks)):
        path = f"{IMAGE_DIR}/{i:03d}.jpg"
        url = urls[i % len(urls)]  # repeat if not enough images
        while url in used and len(used) < len(urls):
            url = random.choice(urls)
        used.add(url)
        if not download_image(url, path):
            # fallback black image
            Image.new("RGB", (1280, 720), (0,0,0)).save(path)

    print("🔊 Generating audio...")
    generate_audio(blocks)

    print("🎬 Creating video...")
    create_video(len(blocks))
    print("✅ FINAL VIDEO READY:", FINAL_VIDEO)

if __name__ == "__main__":
    main()