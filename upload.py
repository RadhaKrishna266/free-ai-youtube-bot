import os
import random
import time
import requests

# ✅ FIX PILLOW ERROR
from PIL import Image
if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = Image.Resampling.LANCZOS

from moviepy.editor import *
from gtts import gTTS

# =========================
# SETUP
# =========================
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

HF_API_KEY = os.getenv("HF_API_KEY")

API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2"
HEADERS = {"Authorization": f"Bearer {HF_API_KEY}"}

# =========================
# STORY (FAST PACED)
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
# VOICE
# =========================
def create_voice(text):
    path = os.path.join(OUTPUT_DIR, "voice.mp3")
    gTTS(text=text, lang='hi').save(path)
    return path

# =========================
# DOWNLOAD AUDIO (BGM)
# =========================
def download_audio(url, filename):
    path = os.path.join(OUTPUT_DIR, filename)
    try:
        r = requests.get(url, timeout=10)
        with open(path, "wb") as f:
            f.write(r.content)
        return path
    except:
        return None

# =========================
# AI IMAGE
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

            print("Retry:", res.text)
            time.sleep(5)

        except Exception as e:
            print("Error:", e)
            time.sleep(5)

    # fallback
    fallback = f"https://picsum.photos/seed/{random.randint(1,9999)}/1080/1920"
    img = requests.get(fallback).content
    with open(img_path, "wb") as f:
        f.write(img)

    return img_path

# =========================
# 🎭 TALKING ANIMATION EFFECT
# =========================
def talking_effect(clip):
    # bounce effect (like speaking)
    clip = clip.set_position(lambda t: ("center", int(10 * (t % 0.3) * 10)))

    # zoom pulse
    clip = clip.resize(lambda t: 1 + 0.05 * (t % 0.5))

    return clip

# =========================
# VIDEO CREATION
# =========================
def create_video(lines, audio_file):
    voice = AudioFileClip(audio_file)
    duration = voice.duration / len(lines)

    clips = []

    BASE_PROMPT = "funny cartoon ghost Champu Bhoot, same character, big eyes, cute, indian village, colorful animation"

    for i, line in enumerate(lines):
        prompt = f"{BASE_PROMPT}, {line}"

        img_path = generate_image(prompt, i)

        clip = ImageClip(img_path).set_duration(duration)

        # 🎭 talking feel
        clip = talking_effect(clip)

        # 🎥 extra zoom
        clip = clip.resize(lambda t: 1 + 0.08 * t)

        # 💥 punchline effect (last scene)
        if i == len(lines) - 1:
            clip = clip.resize(1.2)

        clip = clip.crossfadein(0.2)

        clips.append(clip)

    video = concatenate_videoclips(clips, method="compose")

    # =========================
    # 🎵 BACKGROUND MUSIC
    # =========================
    bgm_url = "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"
    bgm_path = download_audio(bgm_url, "bgm.mp3")

    if bgm_path:
        bgm = AudioFileClip(bgm_path).volumex(0.08)
        final_audio = CompositeAudioClip([voice, bgm])
    else:
        final_audio = voice

    video = video.set_audio(final_audio)

    output = os.path.join(OUTPUT_DIR, "final.mp4")
    video.write_videofile(output, fps=24)

    return output

# =========================
# MAIN
# =========================
def run():
    print("🎭 Creating TALKING Champu Bhoot Video...\n")

    if not HF_API_KEY:
        print("⚠️ HF_API_KEY missing → fallback images will be used")

    lines = generate_story()
    text = " ".join(lines)

    for l in lines:
        print("👉", l)

    audio = create_voice(text)
    print("🎤 Voice ready")

    video = create_video(lines, audio)
    print("🎬 Video created:", video)

    print("\n✅ DONE")


if __name__ == "__main__":
    run()