import os
import subprocess
import textwrap
import requests
from PIL import Image

TOPIC = "Mystery of Stonehenge"

IMAGES_DIR = "images"
AUDIO_FILE = "voice.mp3"
VIDEO_FILE = "final_video.mp4"

MIN_WORDS = 2000
IMAGE_COUNT = 40
IMAGE_DURATION = 8  # seconds per image → ~5–6 min total

os.makedirs(IMAGES_DIR, exist_ok=True)

# -------------------------------------------------
# SCRIPT
# -------------------------------------------------
def generate_long_script(topic):
    para = f"""
    {topic} has puzzled historians for centuries.
    Archaeologists, scientists, and historians continue
    to debate its purpose, construction, and meaning.
    """

    script = " ".join([para] * 150)  # ~2000+ words
    return script.strip()

# -------------------------------------------------
# AUDIO (DUMMY BUT LONG — SAFE FOR CI)
# -------------------------------------------------
def generate_audio(script):
    seconds = IMAGE_COUNT * IMAGE_DURATION

    subprocess.run([
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"sine=frequency=440:duration={seconds}",
        AUDIO_FILE
    ], check=True)

# -------------------------------------------------
# IMAGES
# -------------------------------------------------
def download_images():
    images = []
    for i in range(IMAGE_COUNT):
        path = f"{IMAGES_DIR}/img_{i}.jpg"
        r = requests.get("https://picsum.photos/1920/1080", timeout=10)
        with open(path, "wb") as f:
            f.write(r.content)

        img = Image.open(path).convert("RGB")
        img.save(path, "JPEG")
        images.append(path)

    return images

# -------------------------------------------------
# VIDEO
# -------------------------------------------------
def create_video(images):
    with open("slides.txt", "w") as f:
        for img in images:
            f.write(f"file '{img}'\n")
            f.write(f"duration {IMAGE_DURATION}\n")

    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", "slides.txt",
        "-i", AUDIO_FILE,
        "-vsync", "vfr",
        "-pix_fmt", "yuv420p",
        "-c:v", "libx264",
        "-shortest",
        VIDEO_FILE
    ], check=True)

# -------------------------------------------------
# MAIN
# -------------------------------------------------
def main():
    print("📝 Generating long script...")
    script = generate_long_script(TOPIC)

    print("🔊 Generating long audio...")
    generate_audio(script)

    print("🖼 Downloading images...")
    images = download_images()

    print("🎬 Creating video...")
    create_video(images)

    print("✅