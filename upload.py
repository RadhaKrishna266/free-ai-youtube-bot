import os
import subprocess
import requests
import asyncio
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import edge_tts
from bs4 import BeautifulSoup

# ---------------- CONFIG ----------------
SCRIPT_FILE = "script.txt"
IMAGE_DIR = "images"
AUDIO_DIR = "audio_blocks"
VIDEO_DIR = "video_blocks"
FINAL_VIDEO = "final_video.mp4"
TANPURA_FILE = "audio/tanpura.mp3"  # Make sure this exists
PIXABAY_API_KEY = os.environ.get("PIXABAY_API_KEY")
QUERY = "Vaikunth Vishnu Lakshmi Narayan"
BLOCKS = 5  # Number of blocks/images in video

# ---------------- CREATE FOLDERS ----------------
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
    font = None
    try:
        font = ImageFont.truetype("arial.ttf", 48)
    except:
        pass
    d.text((60, 330), text, fill=(255, 215, 0), font=font)
    img.save(path)

# ---------------- PIXABAY IMAGE FETCH ----------------
def fetch_pixabay_images(query, count):
    url = f"https://pixabay.com/api/?key={PIXABAY_API_KEY}&q={query}&image_type=photo&orientation=horizontal&per_page={count}"
    try:
        res = requests.get(url).json()
        hits = res.get("hits", [])
        if len(hits) < count:
            raise Exception("Not enough images from Pixabay")
        urls = [h["largeImageURL"] for h in hits]
        return urls
    except Exception as e:
        print("⚠ Failed to fetch from Pixabay:", e)
        return []

def download_images(urls):
    paths = []
    for i, url in enumerate(urls):
        path = f"{IMAGE_DIR}/{i:03d}.jpg"
        try:
            r = requests.get(url, timeout=20)
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

# ---------------- PROCESS IMAGES ----------------
def process_images(image_paths):
    processed = []
    for path in image_paths:
        img = Image.open(path)
        # Resize while keeping aspect ratio
        img.thumbnail((1280, 720), Image.Resampling.LANCZOS)
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
    communicate = edge_tts.Communicate(text=text, voice="hi-IN-MadhurNeural")
    await communicate.save(out)

def generate_audio(blocks):
    async def runner():
        for i, text in enumerate(blocks):
            if text.strip():
                await generate_single_audio(text, i)
    asyncio.run(runner())

# ---------------- VIDEO CREATION ----------------
def create_video(image_files, blocks_count):
    clips = []
    for i in range(blocks_count):
        img = image_files[i]
        aud = f"{AUDIO_DIR}/{i:03d}.mp3"
        clip = f"{VIDEO_DIR}/{i:03d}.mp4"
        cmd = [
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
        ]
        run(cmd)
        clips.append(clip)

    # Concatenate clips
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
    # Read script
    blocks = Path(SCRIPT_FILE).read_text(encoding="utf-8").split("\n\n")
    intro = "नमस्कार। स्वागत है आप सभी का VishnuPriya श्रृंखला में। आज हम आपके लिए Vishnu Purana का पहला एपिसोड लाए हैं।"
    outro = "\n\n🙏 अगर आपको यह वीडियो पसंद आया हो, तो कृपया लाइक, शेयर और सब्सक्राइब जरूर करें। हर दिन एक नया एपिसोड आएगा।"
    blocks.insert(0, intro)
    blocks.append(outro)

    # Fetch and process images
    print("🌐 Fetching high-res images from Pixabay...")
    urls = fetch_pixabay_images(QUERY, BLOCKS)
    image_files = download_images(urls)
    image_files = process_images(image_files)

    # Generate audio
    print("🔊 Generating audio blocks...")
    generate_audio(blocks)

    # Create video
    print("🎬 Creating video...")
    create_video(image_files, BLOCKS)

    print("✅ FINAL VIDEO READY:", FINAL_VIDEO)

if __name__ == "__main__":
    main()