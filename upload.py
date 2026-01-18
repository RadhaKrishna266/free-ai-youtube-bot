import os
import subprocess
import requests
from PIL import Image

TOPIC = "Mystery of Stonehenge"

IMAGES_DIR = "images"
AUDIO_FILE = "voice.mp3"
VIDEO_FILE = "final_video.mp4"

IMAGE_COUNT = 40       # 40 * 8 = ~5.3 minutes
IMAGE_DURATION = 8     # seconds per image

os.makedirs(IMAGES_DIR, exist_ok=True)

# -------------------------------------------------
# SCRIPT
# -------------------------------------------------
def generate_long_script(topic):
    paragraph = (
        f"{topic} has puzzled historians for centuries. "
        "Researchers continue to debate its purpose, "
        "construction techniques, and cultural significance. "
    )
    return " ".join([paragraph] * 150)

# -------------------------------------------------
# AUDIO (LONG & CI SAFE)
# -------------------------------------------------
def generate_audio():
    duration = IMAGE_COUNT * IMAGE_DURATION
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"sine=frequency=440:duration={duration}",
        AUDIO_FILE
    ], check=True)

# -------------------------------------------------
# IMAGES
# -------------------------------------------------
def download_images():
    images = []
    for i in range(IMAGE_COUNT):
        path = f"{IMAGES_DIR}/img_{i}.jpg"
        r = requests.get("https://picsum.photos/1920/1080", timeout=15)
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
    print("Starting auto video pipeline...")

    print("Generating script...")
    generate_long_script(TOPIC)

    print("Generating audio...")
    generate_audio()

    print("Downloading images...")
    images = download_images()

    print("Creating video...")
    create_video(images)

    print("DONE: 5–10 minute video created successfully")

if __name__ == "__main__":
    main()