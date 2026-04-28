import os
import random
import requests
import asyncio
import subprocess

import edge_tts

# =========================
# SETUP
# =========================
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

HF_API_KEY = os.getenv("HF_API_KEY")

API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2"
HEADERS = {"Authorization": f"Bearer {HF_API_KEY}"}

W, H = 1080, 1920

# =========================
# STORY
# =========================
def generate_story():
    return [
        "गांव में एक चंपू भूत रहता था...",
        "वो लोगों को डराने नहीं, हंसाने आता था...",
        "एक दिन उसने कहा मैं शादी करूंगा!",
        "अगले दिन सच में बारात आ गई...",
        "भूत बोला - shampoo का खर्चा बच गया 😂"
    ]

# =========================
# TTS
# =========================
async def tts(text, path):
    t = edge_tts.Communicate(text, "hi-IN-SwaraNeural")
    await t.save(path)

def create_voice(text):
    path = f"{OUTPUT_DIR}/voice.mp3"
    asyncio.run(tts(text, path))
    return path

# =========================
# IMAGE GENERATION
# =========================
def build_prompt(line):
    return f"""
    cute funny ghost Champu Bhoot,
    consistent character, white ghost, big eyes,
    indian village cinematic background,
    scene: {line},
    2D cartoon style, vibrant, viral video style
    """

def generate_image(prompt, i):
    path = f"{OUTPUT_DIR}/img_{i}.jpg"

    try:
        r = requests.post(API_URL, headers=HEADERS, json={"inputs": prompt}, timeout=60)

        if r.status_code == 200 and "image" in r.headers.get("content-type", ""):
            with open(path, "wb") as f:
                f.write(r.content)
            return path

    except Exception as e:
        print("Image error:", e)

    # fallback image
    img = requests.get(
        f"https://picsum.photos/1080/1920?random={random.randint(1,9999)}"
    ).content

    with open(path, "wb") as f:
        f.write(img)

    return path

# =========================
# VIDEO CREATION (FFMPEG SAFE)
# =========================
def create_video(images, audio_file):
    print("🎬 Creating video with FFmpeg...")

    # rename images sequentially (IMPORTANT for ffmpeg)
    for i, img in enumerate(images):
        new_name = f"{OUTPUT_DIR}/img_{i}.jpg"
        if img != new_name:
            os.rename(img, new_name)

    video_path = f"{OUTPUT_DIR}/video.mp4"
    final_path = f"{OUTPUT_DIR}/final.mp4"

    # 1️⃣ create image slideshow video
    cmd1 = [
        "ffmpeg", "-y",
        "-framerate", "1/3",
        "-i", f"{OUTPUT_DIR}/img_%d.jpg",
        "-s", "1080x1920",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        video_path
    ]

    print("Running ffmpeg step 1...")
    subprocess.run(cmd1, check=True)

    # 2️⃣ add audio
    cmd2 = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", audio_file,
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        final_path
    ]

    print("Running ffmpeg step 2...")
    subprocess.run(cmd2, check=True)

    return final_path

# =========================
# MAIN
# =========================
def run():
    print("🚀 Starting Shorts Generator...")

    if not HF_API_KEY:
        print("⚠️ HF_API_KEY missing, fallback images will be used")

    lines = generate_story()
    text = " ".join(lines)

    print("🎤 Generating voice...")
    audio = create_voice(text)

    print("🖼 Generating images...")
    images = []
    for i, line in enumerate(lines):
        img = generate_image(build_prompt(line), i)
        images.append(img)

    print("🎬 Building video...")
    video = create_video(images, audio)

    print("✅ DONE VIDEO CREATED:", video)

if __name__ == "__main__":
    run()