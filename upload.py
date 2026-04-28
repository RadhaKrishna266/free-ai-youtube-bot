import os
import random
import requests
import asyncio
import subprocess

import edge_tts

OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

HF_API_KEY = os.getenv("HF_API_KEY")

API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2"
HEADERS = {"Authorization": f"Bearer {HF_API_KEY}"}

# =========================
# STORY
# =========================
def generate_story():
    return [
        "गांव में एक चंपू भूत रहता था...",
        "वो डराने नहीं, लोगों को हंसाने आता था...",
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
    cartoon style, vibrant colors, 2D animation
    """

def generate_image(prompt, i):
    path = f"{OUTPUT_DIR}/img_{i}.jpg"

    try:
        r = requests.post(API_URL, headers=HEADERS, json={"inputs": prompt}, timeout=60)

        if r.status_code == 200 and "image" in r.headers.get("content-type", ""):
            with open(path, "wb") as f:
                f.write(r.content)
            return path

    except:
        pass

    # fallback
    img = requests.get(
        f"https://picsum.photos/1080/1920?random={random.randint(1,9999)}"
    ).content

    with open(path, "wb") as f:
        f.write(img)

    return path

# =========================
# FFMPEG VIDEO BUILD
# =========================
def create_video(images, audio_file):
    list_file = f"{OUTPUT_DIR}/list.txt"

    duration = 3  # seconds per scene

    with open(list_file, "w") as f:
        for img in images:
            f.write(f"file '{img}'\n")
            f.write(f"duration {duration}\n")
        f.write(f"file '{images[-1]}'\n")

    temp_video = f"{OUTPUT_DIR}/temp.mp4"
    final_video = f"{OUTPUT_DIR}/final.mp4"

    # Create video from images
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", list_file,
        "-vsync", "vfr",
        "-pix_fmt", "yuv420p",
        "-s", "1080x1920",
        temp_video
    ])

    # Add audio
    subprocess.run([
        "ffmpeg", "-y",
        "-i", temp_video,
        "-i", audio_file,
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        final_video
    ])

    return final_video

# =========================
# MAIN
# =========================
def run():
    print("🎬 Starting YouTube Shorts Bot...")

    lines = generate_story()
    text = " ".join(lines)

    audio = create_voice(text)
    print("🎤 Voice ready")

    images = []
    for i, line in enumerate(lines):
        img = generate_image(build_prompt(line), i)
        images.append(img)

    print("🖼 Images ready")

    video = create_video(images, audio)

    print("✅ DONE:", video)

if __name__ == "__main__":
    run()