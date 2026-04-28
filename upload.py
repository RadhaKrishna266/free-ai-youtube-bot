import os
import random
import time
import requests
import asyncio

from PIL import Image
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

W, H = 1080, 1920  # 🎯 YouTube Shorts format

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
# PROMPT (consistent character)
# =========================
def build_prompt(line):
    return f"""
    cute funny ghost character Champu Bhoot,
    same character consistency, white glowing ghost, big expressive eyes,
    indian village cinematic background,
    scene: {line},
    ultra detailed, 2D animation style, vibrant colors
    """

# =========================
# EDGE TTS
# =========================
async def tts_async(text, path):
    tts = edge_tts.Communicate(text, "hi-IN-SwaraNeural")
    await tts.save(path)

def create_voice(text):
    path = os.path.join(OUTPUT_DIR, "voice.mp3")
    asyncio.run(tts_async(text, path))
    return path

# =========================
# IMAGE GENERATION
# =========================
def generate_image(prompt, i):
    path = os.path.join(OUTPUT_DIR, f"{i}.jpg")

    try:
        res = requests.post(API_URL, headers=HEADERS, json={"inputs": prompt}, timeout=60)

        if res.status_code == 200 and "image" in res.headers.get("content-type", ""):
            with open(path, "wb") as f:
                f.write(res.content)
            return path

    except:
        pass

    # fallback
    img = requests.get(f"https://picsum.photos/1080/1920?random={random.randint(1,9999)}").content
    with open(path, "wb") as f:
        f.write(img)

    return path

# =========================
# TIMING
# =========================
def get_durations(lines, total):
    base = total / len(lines)
    return [base]*len(lines)

# =========================
# SIMPLE CLEAN EFFECT (IMPORTANT FIX)
# =========================
def animate(clip):
    return clip.resize(height=H).set_position("center")

# =========================
# VIDEO CREATION
# =========================
def create_video(lines, audio_file):
    audio = AudioFileClip(audio_file)

    durations = get_durations(lines, audio.duration)
    clips = []

    for i, line in enumerate(lines):
        img = generate_image(build_prompt(line), i)

        clip = ImageClip(img).set_duration(durations[i])

        clip = animate(clip)

        # smooth transition
        clip = clip.crossfadein(0.2)

        clips.append(clip)

    video = concatenate_videoclips(clips, method="compose")

    video = video.set_audio(audio)

    output = os.path.join(OUTPUT_DIR, "final.mp4")

    video.write_videofile(
        output,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        preset="ultrafast",
        threads=2
    )

    return output

# =========================
# MAIN
# =========================
def run():
    print("🎬 Creating YouTube Shorts Video (1080x1920)...")

    lines = generate_story()

    text = " ".join(lines)

    audio = create_voice(text)
    print("🎤 Voice ready")

    video = create_video(lines, audio)
    print("✅ DONE:", video)

if __name__ == "__main__":
    run()