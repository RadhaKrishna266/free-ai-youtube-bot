import os
import subprocess
import requests
import asyncio
from pathlib import Path
from PIL import Image, ImageDraw
import edge_tts

# ---------------- CONFIG ----------------
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

# ---------------- PLACEHOLDER ----------------
def placeholder(path, text="ॐ नमो नारायणाय"):
    img = Image.new("RGB", (1280, 720), (10, 5, 0))
    d = ImageDraw.Draw(img)
    d.text((60, 330), text, fill=(255, 215, 0))
    img.save(path)

# ---------------- DOWNLOAD VISHNU IMAGES ----------------
def download_images(blocks):
    print("🖼 Downloading AUTHENTIC Vishnu / Vaikuntha images...")

    queries = [
        "Vishnu Purana book illustration",
        "Lord Vishnu painting",
        "Vishnu Dashavatara illustration",
        "Vishnu cosmic form painting",
        "Vaikuntha lok painting",
    ]

    all_hits = []
    seen_urls = set()

    for q in queries:
        try:
            r = requests.get(
                "https://pixabay.com/api/",
                params={
                    "key": PIXABAY_API_KEY,
                    "q": q,
                    "image_type": "photo",
                    "orientation": "horizontal",
                    "safesearch": "true",
                    "per_page": 50
                },
                timeout=15
            ).json()

            for h in r.get("hits", []):
                url = h.get("largeImageURL")
                tags = h.get("tags", "").lower()
                if url and url not in seen_urls and any(k in tags for k in ["vishnu", "narayana", "dashavatara", "vaikuntha", "hindu god"]):
                    all_hits.append(h)
                    seen_urls.add(url)
        except Exception as e:
            print("⚠️ Pixabay request failed:", e)

    if not all_hits:
        raise RuntimeError("❌ No Vishnu images found. Check PIXABAY_API_KEY or internet")

    print(f"✅ {len(all_hits)} Vishnu images collected")

    for i, text in enumerate(blocks):
        path = f"{IMAGE_DIR}/{i:03d}.jpg"
        try:
            hit = all_hits[i % len(all_hits)]
            img_data = requests.get(hit["largeImageURL"], timeout=15).content
            with open(path, "wb") as f:
                f.write(img_data)
        except Exception as e:
            print(f"⚠️ Failed to download image {i}, using placeholder:", e)
            placeholder(path, text)

# ---------------- HINDI NEURAL VOICE ----------------
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
    print("🎞 Creating final video...")
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
    print("✅ FINAL VISHNU PURANA VIDEO READY:", FINAL_VIDEO)
    print("🕉️ Remember: Daily episodes will be uploaded. Like, share, subscribe!")

if __name__ == "__main__":
    main()