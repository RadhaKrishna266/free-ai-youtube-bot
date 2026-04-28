import os
import random
import time
import requests
import asyncio

# Pillow fix
from PIL import Image
if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = Image.Resampling.LANCZOS

from moviepy.editor import *
import edge_tts

# =========================
# SETUP
# =========================
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
        "वो लोगों को डराने नहीं, हंसाने के लिए famous था...",
        "एक दिन उसने बोला — मैं शादी करूंगा!",
        "अगले दिन सच में बारात आ गई...",
        "भूत बोला — shampoo का खर्चा बचेगा 😂"
    ]

# =========================
# BETTER PROMPT
# =========================
def build_prompt(line):
    return f"""
    funny cartoon ghost Champu Bhoot,
    same character, white ghost, big eyes, cute face,
    indian village background,
    scene showing: {line},
    colorful cartoon, 2D animation style
    """

# =========================
# NATURAL VOICE (EDGE TTS)
# =========================
async def tts_async(text, path):
    communicate = edge_tts.Communicate(text, "hi-IN-SwaraNeural")
    await communicate.save(path)

def create_voice(text):
    path = os.path.join(OUTPUT_DIR, "voice.mp3")
    asyncio.run(tts_async(text, path))
    return path

# =========================
# IMAGE GENERATION
# =========================
def generate_image(prompt, index):
    img_path = os.path.join(OUTPUT_DIR, f"{index}.jpg")

    payload = {"inputs": prompt}

    for _ in range(3):
        try:
            res = requests.post(API_URL, headers=HEADERS, json=payload, timeout=60)

            if res.status_code == 200:
                with open(img_path, "wb") as f:
                    f.write(res.content)
                return img_path

            time.sleep(5)

        except:
            time.sleep(5)

    # fallback
    fallback = f"https://picsum.photos/seed/{random.randint(1,9999)}/1080/1920"
    img = requests.get(fallback).content
    with open(img_path, "wb") as f:
        f.write(img)

    return img_path

# =========================
# TIMING FIX
# =========================
def get_durations(lines, total_audio):
    base = total_audio / len(lines)
    durations = []

    for i in range(len(lines)):
        if i == len(lines) - 1:
            durations.append(base + 1.2)  # punchline pause
        else:
            durations.append(base)

    return durations

# =========================
# TALKING EFFECT
# =========================
def talking_effect(clip):
    clip = clip.set_position(lambda t: ("center", int(5 * (t % 0.4) * 10)))
    clip = clip.resize(lambda t: 1 + 0.03 * (t % 0.5))
    return clip

# =========================
# VIDEO CREATION
# =========================
def create_video(lines, audio_file):
    voice = AudioFileClip(audio_file)

    durations = get_durations(lines, voice.duration)
    clips = []

    for i, line in enumerate(lines):
        prompt = build_prompt(line)
        img_path = generate_image(prompt, i)

        clip = ImageClip(img_path).set_duration(durations[i])

        clip = talking_effect(clip)

        if i == len(lines) - 1:
            clip = clip.resize(1.1)  # punch zoom

        clip = clip.crossfadein(0.2)

        clips.append(clip)

    video = concatenate_videoclips(clips, method="compose")

    video = video.set_audio(voice)

    output = os.path.join(OUTPUT_DIR, "final.mp4")
    video.write_videofile(output, fps=24)

    return output

# =========================
# MAIN
# =========================
def run():
    print("🎬 Creating FINAL Champu Bhoot Video...\n")

    if not HF_API_KEY:
        print("⚠️ HF_API_KEY missing → fallback images will be used")

    lines = generate_story()
    text = " ".join(lines)

    for l in lines:
        print("👉", l)

    audio = create_voice(text)
    print("🎤 Natural voice created")

    video = create_video(lines, audio)
    print("🎬 Video created:", video)

    print("\n✅ DONE - Download from GitHub Actions")


if __name__ == "__main__":
    run()