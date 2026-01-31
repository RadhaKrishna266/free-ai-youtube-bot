import os
import subprocess
import requests
import asyncio
from pathlib import Path
from PIL import Image, ImageDraw
import edge_tts
from io import BytesIO

SCRIPT_FILE = "script.txt"
IMAGE_DIR = "images"
AUDIO_DIR = "audio_blocks"
VIDEO_DIR = "video_blocks"
FINAL_VIDEO = "final_video.mp4"

PIXABAY_API_KEY = os.environ.get("PIXABAY_API_KEY")

os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)

# ---------------- UTILS ----------------
def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)

def safe_get_json(url, params):
    try:
        r = requests.get(url, params=params, timeout=15)
        if r.status_code != 200 or not r.text.strip().startswith("{"):
            return None
        return r.json()
    except Exception:
        return None

# ---------------- PLACEHOLDER ----------------
def placeholder(path, text="ॐ नमो नारायणाय"):
    img = Image.new("RGB", (1280, 720), (15, 10, 5))
    d = ImageDraw.Draw(img)
    d.text((420, 330), text, fill=(255, 215, 0))
    img.save(path)

# ---------------- IMAGE COLLECTION ----------------
def collect_pixabay_images(query, limit):
    data = safe_get_json(
        "https://pixabay.com/api/",
        {
            "key": PIXABAY_API_KEY,
            "q": query,
            "image_type": "photo",
            "orientation": "horizontal",
            "safesearch": "true",
            "per_page": limit
        }
    )
    if not data:
        return []

    images = []
    for h in data.get("hits", []):
        tags = h.get("tags", "").lower()
        if "vishnu" in tags or "narayana" in tags or "krishna" in tags:
            images.append(h["largeImageURL"])
    return images

# ---------------- DOWNLOAD IMAGES ----------------
def download_images(blocks):
    print("🖼 Downloading AUTHENTIC Vishnu Purana images (NO repeats)...")

    used = set()
    collected = []

    # 1️⃣ Vishnu Purana manuscript / book FIRST
    book_imgs = collect_pixabay_images("Vishnu Purana manuscript book", 10)
    if book_imgs:
        collected.append(book_imgs[0])
        used.add(book_imgs[0])

    # 2️⃣ Vishnu, Vaikuntha, Dashavatara
    queries = [
        "Lord Vishnu painting",
        "Vishnu Vaikuntha painting",
        "Vishnu Dashavatara painting",
        "Vishnu cosmic form painting"
    ]

    for q in queries:
        imgs = collect_pixabay_images(q, 30)
        for img in imgs:
            if img not in used:
                collected.append(img)
                used.add(img)

    if not collected:
        raise RuntimeError("❌ No Vishnu images found. Check Pixabay API key.")

    print(f"✅ {len(collected)} unique Vishnu images collected")

    for i, text in enumerate(blocks):
        path = f"{IMAGE_DIR}/{i:03d}.jpg"
        if i < len(collected):
            try:
                img = requests.get(collected[i], timeout=20).content
                Image.open(BytesIO(img)).convert("RGB").save(path)
            except Exception:
                placeholder(path)
        else:
            placeholder(path)

# ---------------- AUDIO ----------------
async def generate_single_audio(text, index):
    out = f"{AUDIO_DIR}/{index:03d}.wav"
    communicate = edge_tts.Communicate(
        text=text,
        voice="hi-IN-MadhurNeural",
        rate="+0%",
        pitch="+0Hz"
    )
    await communicate.save(out)

def generate_audio(blocks):
    print("🎙 Generating HIGH-QUALITY Hindi Neural voice...")
    async def runner():
        for i, text in enumerate(blocks):
            if text.strip():
                await generate_single_audio(text, i)
    asyncio.run(runner())

# ---------------- VIDEO ----------------
def create_video(blocks):
    print("🎞 Creating FINAL video...")
    clips = []

    for i in range(len(blocks)):
        clip = f"{VIDEO_DIR}/{i:03d}.mp4"
        run([
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", f"{IMAGE_DIR}/{i:03d}.jpg",
            "-i", f"{AUDIO_DIR}/{i:03d}.wav",
            "-vf", "scale=1280:720,format=yuv420p",
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
    download_images(blocks)
    generate_audio(blocks)
    create_video(blocks)
    print("✅ FINAL EPISODE-1 VISHNU PURANA VIDEO READY:", FINAL_VIDEO)

if __name__ == "__main__":
    main()