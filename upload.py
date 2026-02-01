import os
import subprocess
import asyncio
from pathlib import Path
from PIL import Image
import requests
from bs4 import BeautifulSoup
import edge_tts

# ---------------- CONFIG ----------------
SCRIPT_FILE = "script.txt"
IMAGE_DIR = "images"
AUDIO_DIR = "audio_blocks"
VIDEO_DIR = "video_blocks"
FINAL_VIDEO = "final_video.mp4"
TANPURA_FILE = "audio/tanpura.mp3"  # Your already added tanpura.mp3
TANPURA_VOLUME = 0.2  # Reduce tanpura volume
GOOGLE_SEARCH_URL = "https://www.google.com/search?q=vaikunth+vishnu+vishnu+avtara+lakshmi+vishnh+animated+wallpapers+only+photos+without+text+high+resolution+only+clear+images+no+thumbnail+of+website+on+image&tbm=isch"
BLOCKS = 10  # Number of script blocks / images to use

# ---------------- CREATE FOLDERS ----------------
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)

# ---------------- UTILS ----------------
def run(cmd):
    print("▶ Running command:", " ".join(cmd))
    subprocess.run(cmd, check=True)

# ---------------- IMAGE FETCHING ----------------
def fetch_google_images(url, count):
    print("🌐 Fetching high-res images from Google...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "lxml")
    imgs = soup.find_all("img")
    urls = []
    for img in imgs:
        src = img.get("src")
        if src and src.startswith("http"):
            urls.append(src)
        if len(urls) >= count:
            break

    if len(urls) < count:
        raise Exception("❌ Not enough images fetched from Google")

    paths = []
    for i, u in enumerate(urls):
        out = f"{IMAGE_DIR}/{i:03d}.jpg"
        r = requests.get(u, stream=True)
        with open(out, "wb") as f:
            for chunk in r.iter_content(1024):
                f.write(chunk)
        paths.append(out)
    print(f"✅ {len(paths)} images downloaded successfully")
    return paths

# ---------------- PROCESS IMAGES ----------------
def process_images(image_paths):
    processed = []
    for path in image_paths:
        img = Image.open(path)
        # Resize while keeping aspect ratio
        img.thumbnail((1280, 720), Image.ANTIALIAS)
        # Ensure width & height divisible by 2
        new_w = img.width + img.width % 2
        new_h = img.height + img.height % 2
        new_img = Image.new("RGB", (new_w, new_h), (0, 0, 0))  # black background
        new_img.paste(img, ((new_w - img.width)//2, (new_h - img.height)//2))
        new_img.save(path)
        processed.append(path)
    return processed

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
    print(f"✅ Audio blocks generated")

# ---------------- VIDEO CREATION ----------------
def create_video(images, num_blocks):
    clips = []
    for i in range(num_blocks):
        img = images[i]
        aud = f"{AUDIO_DIR}/{i:03d}.mp3"
        clip = f"{VIDEO_DIR}/{i:03d}.mp4"
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", img,
            "-i", aud,
            "-i", TANPURA_FILE,
            "-filter_complex",
            f"[2:a]volume={TANPURA_VOLUME}[a2];[1:a][a2]amix=inputs=2:duration=first:dropout_transition=2[a]",
            "-map", "0:v",
            "-map", "[a]",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-shortest",
            clip
        ]
        run(cmd)
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
    print(f"✅ FINAL VIDEO READY: {FINAL_VIDEO}")

# ---------------- MAIN ----------------
def main():
    blocks = Path(SCRIPT_FILE).read_text(encoding="utf-8").split("\n\n")
    intro = "नमस्कार। स्वागत है आप सभी का VishnuPriya श्रृंखला में। आज हम आपके लिए Vishnu Purana का पहला एपिसोड लाए हैं।"
    outro = "\n\n🙏 अगर आपको यह वीडियो पसंद आया हो, तो कृपया लाइक, शेयर और सब्सक्राइब जरूर करें। हर दिन एक नया एपिसोड आएगा।"
    blocks.insert(0, intro)
    blocks.append(outro)

    # Fetch images from Google
    image_files = fetch_google_images(GOOGLE_SEARCH_URL, len(blocks))
    image_files = process_images(image_files)

    # Generate audio
    generate_audio(blocks)

    # Create video
    create_video(image_files, len(blocks))

if __name__ == "__main__":
    main()
