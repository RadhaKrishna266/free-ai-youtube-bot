import os
import subprocess
import asyncio
from pathlib import Path
import requests
from PIL import Image, ImageDraw

import edge_tts

# ---------------- CONFIG ----------------
SCRIPT_FILE = "script.txt"           # Your shlok + arth + bhavarth file
IMAGE_DIR = "images"
AUDIO_DIR = "audio_blocks"
VIDEO_DIR = "video_blocks"
FINAL_VIDEO = "final_video.mp4"

os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)

# ---------------- CURATED VISHNU / VAIKUNTH IMAGES ----------------
VISHNU_IMAGES = [
    "https://upload.wikimedia.org/wikipedia/commons/2/23/Vishnu_Purana_cover.jpg",        # Vishnu Purana book cover
    "https://upload.wikimedia.org/wikipedia/commons/1/1b/Vishnu_dashavatara_1.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/3/36/Vishnu_cosmic_form.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/5/50/Vaikuntha_painting.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/7/71/Vishnu_Purana_manuscript_illustration.jpg",
    # Add more URLs of authentic Vishnu illustrations for no repeats
]

# ---------------- UTILS ----------------
def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)

def placeholder(path, text):
    img = Image.new("RGB", (1280, 720), (10, 5, 0))
    d = ImageDraw.Draw(img)
    d.text((60, 330), "ॐ नमो नारायणाय", fill=(255, 215, 0))
    img.save(path)

# ---------------- DOWNLOAD IMAGES ----------------
def download_images(blocks):
    print("🖼 Downloading AUTHENTIC Vishnu / Vaikuntha images...")
    if not VISHNU_IMAGES:
        raise RuntimeError("No curated Vishnu images provided!")

    for i, text in enumerate(blocks):
        path = f"{IMAGE_DIR}/{i:03d}.jpg"
        url = VISHNU_IMAGES[i % len(VISHNU_IMAGES)]  # no repeats if enough images
        try:
            img_data = requests.get(url).content
            with open(path, "wb") as f:
                f.write(img_data)
        except:
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

# ---------------- VIDEO CREATION ----------------
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
    print("✅ EPISODE 1 OF VISHNUPRIYA SERIES READY:", FINAL_VIDEO)
    print("📢 Daily we will upload one episode of Vishnupriya series with shlok + arth + bhavarth.")
    print("🙏 Please like, share, and subscribe for more devotional videos!")

if __name__ == "__main__":
    main()