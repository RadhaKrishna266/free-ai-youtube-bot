import os
import asyncio
import requests
from pathlib import Path
from PIL import Image, ImageDraw
import subprocess
from edge_tts import Communicate

# ================= PATHS =================
SCRIPT_FILE = "script.txt"
IMAGE_DIR = "images"
AUDIO_DIR = "audio_blocks"
VIDEO_DIR = "video_blocks"
FINAL_VIDEO = "final_video.mp4"

PIXABAY_API_KEY = os.environ.get("PIXABAY_API_KEY")

os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)

# ================= UTILS =================
def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)

# ================= PLACEHOLDER IMAGE =================
def placeholder(path, text):
    img = Image.new("RGB", (1280, 720), (15, 10, 5))
    d = ImageDraw.Draw(img)
    d.text((40, 340), text[:80], fill=(255, 200, 0))
    img.save(path)

# ================= DOWNLOAD IMAGES =================
def download_images(blocks):
    print("🖼 Downloading devotional images...")
    r = requests.get(
        "https://pixabay.com/api/",
        params={
            "key": PIXABAY_API_KEY,
            "q": "Lord Vishnu Krishna Hindu devotional art painting",
            "image_type": "photo",
            "orientation": "horizontal",
            "safesearch": "true",
            "per_page": 50
        }
    ).json()

    hits = r.get("hits", [])
    for i, text in enumerate(blocks):
        path = f"{IMAGE_DIR}/{i:03d}.jpg"
        try:
            if hits:
                img = requests.get(hits[i % len(hits)]["largeImageURL"]).content
                with open(path, "wb") as f:
                    f.write(img)
            else:
                placeholder(path, text)
        except:
            placeholder(path, text)

# ================= EDGE TTS (Hindi Neural Voice) =================
async def generate_single_audio(text, i):
    out_file = f"{AUDIO_DIR}/{i:03d}.wav"
    communicate = Communicate(text, voice="hi-IN-MadhurNeural")
    await communicate.save(out_file)

def generate_audio(blocks):
    print("🎙 Generating REAL Hindi Neural voice...")
    os.makedirs(AUDIO_DIR, exist_ok=True)
    tasks = [asyncio.create_task(generate_single_audio(text, i))
             for i, text in enumerate(blocks) if text.strip()]
    asyncio.run(asyncio.gather(*tasks))

# ================= CREATE VIDEO =================
def create_video(blocks):
    print("🎞 Creating video...")
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

# ================= MAIN =================
def main():
    blocks = Path(SCRIPT_FILE).read_text(encoding="utf-8").split("\n\n")
    download_images(blocks)
    generate_audio(blocks)
    create_video(blocks)
    print("✅ FINAL VIDEO READY:", FINAL_VIDEO)

if __name__ == "__main__":
    main()