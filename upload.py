import os
import random
import requests
from moviepy.editor import *
from gtts import gTTS

OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

# =========================
# STORY
# =========================
def generate_story():
    return [
        "एक मजेदार चुड़ैल गांव में रहती थी...",
        "कोई उससे डरता नहीं था...",
        "एक दिन उसने शादी करने का फैसला किया...",
        "पूरा गांव हैरान रह गया...",
        "लड़का बोला — shampoo का खर्चा बचेगा 😂"
    ]

# =========================
# VOICE
# =========================
def create_voice(text):
    path = os.path.join(OUTPUT_DIR, "voice.mp3")
    tts = gTTS(text=text, lang='hi')
    tts.save(path)
    return path

# =========================
# DOWNLOAD IMAGE
# =========================
def get_image(query, index):
    url = f"https://api.pexels.com/v1/search?query={query}&per_page=1"
    headers = {"Authorization": PEXELS_API_KEY}
    res = requests.get(url, headers=headers).json()

    img_url = res["photos"][0]["src"]["portrait"]
    img_path = os.path.join(OUTPUT_DIR, f"{index}.jpg")

    img_data = requests.get(img_url).content
    with open(img_path, "wb") as f:
        f.write(img_data)

    return img_path

# =========================
# CREATE ANIMATED VIDEO
# =========================
def create_video(lines, audio_file):
    audio = AudioFileClip(audio_file)
    duration = audio.duration / len(lines)

    clips = []

    for i, line in enumerate(lines):
        img_path = get_image("cartoon village funny", i)

        clip = ImageClip(img_path).set_duration(duration)

        # Zoom effect (animation feel)
        clip = clip.resize(lambda t: 1 + 0.1*t)

        clips.append(clip)

    video = concatenate_videoclips(clips)
    video = video.set_audio(audio)

    output_path = os.path.join(OUTPUT_DIR, "final.mp4")
    video.write_videofile(output_path, fps=24)

    return output_path

# =========================
# MAIN
# =========================
def run():
    print("🎬 Creating Animation Video...")

    lines = generate_story()
    text = " ".join(lines)

    audio = create_voice(text)
    video = create_video(lines, audio)

    print("✅ DONE:", video)

if __name__ == "__main__":
    run()