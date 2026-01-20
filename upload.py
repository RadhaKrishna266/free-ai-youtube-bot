import os
import subprocess
import textwrap
import requests
import random

PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY")

IMAGES_DIR = "images"
VOICE_WAV = "voice.wav"
VOICE_M4A = "voice.m4a"
FINAL_VIDEO = "final.mp4"

DURATION_MINUTES = 10
FPS = 25
IMG_DURATION = 5  # seconds per image

os.makedirs(IMAGES_DIR, exist_ok=True)

FACTS = [
    "Octopuses have three hearts and blue blood.",
    "Bananas are berries but strawberries are not.",
    "The human brain can generate enough electricity to power a small bulb.",
    "There are more trees on Earth than stars in the Milky Way.",
    "Honey never spoils and was found in ancient Egyptian tombs.",
    "Sharks existed before trees.",
    "A day on Venus is longer than a year on Venus.",
    "Wombat poop is cube-shaped.",
]

def build_script():
    repeat = (DURATION_MINUTES * 60) // 15
    script = []
    for _ in range(repeat):
        script.append(random.choice(FACTS))
    return " ".join(script)

def download_images(query="nature"):
    print("🖼️ Downloading images")
    url = "https://pixabay.com/api/"
    params = {
        "key": PIXABAY_API_KEY,
        "q": query,
        "image_type": "photo",
        "per_page": 60
    }
    r = requests.get(url, params=params).json()
    for i, hit in enumerate(r["hits"][:60]):
        img = requests.get(hit["largeImageURL"]).content
        with open(f"{IMAGES_DIR}/{i}.jpg", "wb") as f:
            f.write(img)

def create_voice(text):
    print("🎙️ Creating REAL voice with Piper")

    with open("script.txt", "w") as f:
        f.write(text)

    subprocess.run([
        "./piper/piper",
        "--model", "./piper/en_US-lessac-medium.onnx",
        "--output_file", VOICE_WAV
    ], input=text.encode(), check=True)

    subprocess.run([
        "ffmpeg", "-y",
        "-i", VOICE_WAV,
        VOICE_M4A
    ], check=True)

def create_video():
    print("🎬 Creating 10-minute video")

    img_pattern = f"{IMAGES_DIR}/%d.jpg"

    subprocess.run([
        "ffmpeg", "-y",
        "-framerate", f"{FPS}",
        "-i", img_pattern,
        "-i", VOICE_M4A,
        "-vf", "zoompan=z='min(zoom+0.0005,1.1)':d=125",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-shortest",
        FINAL_VIDEO
    ], check=True)

def main():
    print("🚀 AI FACT VIDEO BOT (REAL VOICE)")
    script = build_script()
    download_images("science facts")
    create_voice(script)
    create_video()
    print("✅ DONE →", FINAL_VIDEO)

if __name__ == "__main__":
    main()