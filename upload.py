import os
import subprocess
import requests
import asyncio
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import edge_tts

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
def placeholder(path, text):
    img = Image.new("RGB", (1280, 720), (10, 5, 0))
    d = ImageDraw.Draw(img)
    d.text((60, 330), "ॐ नमो नारायणाय", fill=(255, 215, 0))
    img.save(path)

# ---------------- DOWNLOAD VISHNU IMAGES ----------------
def download_images(blocks):
    print("🖼 Downloading PURE Lord Vishnu / Vishnu Purana images...")

    queries = [
        "Lord Vishnu painting",
        "Vishnu Purana illustration",
        "Vishnu cosmic form painting",
        "Vishnu Dashavatara painting",
        "Vishnu Hindu mythology art"
    ]

    all_hits = []

    for q in queries:
        r = requests.get(
            "https://pixabay.com/api/",
            params={
                "key": PIXABAY_API_KEY,
                "q": q,
                "image_type": "photo",
                "orientation": "horizontal",
                "safesearch": "true",
                "per_page": 20
            }
        ).json()

        for h in r.get("hits", []):
            tags = h.get("tags", "").lower()
            if any(k in tags for k in ["vishnu", "narayana", "dashavatara", "hindu god"]):
                all_hits.append(h)

    if not all_hits:
        raise RuntimeError("❌ No Vishnu images found from Pixabay")

    print(f"✅ {len(all_hits)} Vishnu images collected")

    for i, text in enumerate(blocks):
        path = f"{IMAGE_DIR}/{i:03d}.jpg"
        hit = all_hits[i % len(all_hits)]
        img = requests.get(hit["largeImageURL"]).content
        with open(path, "wb") as f:
            f.write(img)

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
    print("🎙 Generating HIGH-QUALITY Hindi Neural voice (Vishnu style)...")

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
    print("✅ FINAL VISHNU VIDEO READY:", FINAL_VIDEO)

if __name__ == "__main__":
    main()