import os
import random
import time
import requests
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
# STORY
# =========================
def generate_story():
    stories = [
        [
            "गांव में एक चंपू भूत रहता था...",
            "वो लोगों को डराने नहीं, हंसाने के लिए famous था...",
            "एक दिन उसने शादी करने का फैसला किया...",
            "पूरा गांव हैरान रह गया...",
            "भूत बोला — shampoo का खर्चा बचेगा 😂"
        ],
        [
            "चंपू भूत नौकरी ढूंढ रहा था...",
            "HR ने पूछा — experience?",
            "भूत बोला — 100 साल से लोगों को परेशान कर रहा हूँ 😂",
            "HR बोला — तुम overqualified हो!",
            "सब हंस पड़े 😂"
        ]
    ]
    return random.choice(stories)

# =========================
# VOICE
# =========================
def create_voice(text):
    path = os.path.join(OUTPUT_DIR, "voice.mp3")
    gTTS(text=text, lang='hi').save(path)
    return path

# =========================
# AI IMAGE GENERATION
# =========================
def generate_image(prompt, index):
    img_path = os.path.join(OUTPUT_DIR, f"{index}.jpg")

    payload = {"inputs": prompt}

    for attempt in range(3):
        try:
            response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=60)

            if response.status_code == 200:
                with open(img_path, "wb") as f:
                    f.write(response.content)
                return img_path

            print("Retry:", response.text)
            time.sleep(5)

        except Exception as e:
            print("Error:", e)
            time.sleep(5)

    # fallback
    print("⚠️ Using fallback image")
    fallback = f"https://picsum.photos/seed/{random.randint(1,9999)}/1080/1920"
    img = requests.get(fallback).content
    with open(img_path, "wb") as f:
        f.write(img)

    return img_path

# =========================
# VIDEO CREATION
# =========================
def create_video(lines, audio_file):
    audio = AudioFileClip(audio_file)
    duration = audio.duration / len(lines)

    clips = []

    BASE_PROMPT = "funny cartoon ghost Champu Bhoot, same character, big eyes, cute, indian village, colorful animation"

    for i, line in enumerate(lines):
        prompt = f"{BASE_PROMPT}, scene: {line}"

        img_path = generate_image(prompt, i)

        clip = ImageClip(img_path).set_duration(duration)

        # Animation feel
        clip = clip.resize(lambda t: 1 + 0.1 * t)
        clip = clip.crossfadein(0.4)

        clips.append(clip)

    video = concatenate_videoclips(clips, method="compose")
    video = video.set_audio(audio)

    output = os.path.join(OUTPUT_DIR, "final.mp4")
    video.write_videofile(output, fps=24)

    return output

# =========================
# MAIN
# =========================
def run():
    print("👻 Creating Champu Bhoot AI Video...\n")

    lines = generate_story()
    text = " ".join(lines)

    for l in lines:
        print("👉", l)

    audio = create_voice(text)
    print("🎤 Voice created")

    video = create_video(lines, audio)
    print("🎬 Video created:", video)

    print("\n✅ DONE")


if __name__ == "__main__":
    run()