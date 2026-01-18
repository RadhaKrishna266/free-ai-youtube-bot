import os
import random
import subprocess
from PIL import Image, ImageDraw

# ================= CONFIG =================

WIDTH, HEIGHT = 1920, 1080
FPS = 25
VOICE = "en-IN-PrabhatNeural"
IMAGE_COUNT = 60
IMAGE_DURATION = 6  # seconds per image

TOPICS = [
    "Mystery of Stonehenge",
    "Secrets of Egyptian Pyramids",
    "Lost City of Atlantis",
    "Ancient Roman Colosseum"
]

# ================= SCRIPT =================

def generate_script(topic):
    paragraphs = []
    for _ in range(25):
        paragraphs.append(
            f"{topic} has fascinated historians for centuries. "
            f"This section explores its history, theories, construction, "
            f"and mysteries that remain unsolved even today."
        )

    script = "\n\n".join(paragraphs)

    with open("script.txt", "w", encoding="utf-8") as f:
        f.write(script)

# ================= VOICE =================

def generate_voice():
    subprocess.run([
        "edge-tts",
        "--voice", VOICE,
        "--file", "script.txt",
        "--write-media", "voice.mp3"
    ], check=True)

# ================= IMAGES =================

def generate_images(topic):
    os.makedirs("images", exist_ok=True)
    paths = []

    for i in range(IMAGE_COUNT):
        img = Image.new("RGB", (WIDTH, HEIGHT), (15, 15, 15))
        draw = ImageDraw.Draw(img)

        draw.text(
            (WIDTH//2 - 400, HEIGHT//2 - 20),
            topic.upper(),
            fill=(255, 255, 255)
        )

        path = f"images/img_{i}.png"
        img.save(path)
        paths.append(path)

    return paths

# ================= VIDEO =================

def create_video(images):
    with open("images.txt", "w") as f:
        for img in images:
            f.write(f"file '{img}'\n")
            f.write(f"duration {IMAGE_DURATION}\n")

    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", "images.txt",
        "-vf", "scale=1920:1080,format=yuv420p",
        "-r", str(FPS),
        "-c:v", "libx264",
        "video.mp4"
    ], check=True)

    subprocess.run([
        "ffmpeg", "-y",
        "-i", "video.mp4",
        "-i", "voice.mp3",
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        "final.mp4"
    ], check=True)

# ================= MAIN =================

def main():
    print("🚀 Starting auto video pipeline")

    topic = random.choice(TOPICS)
    print("Topic:", topic)

    generate_script(topic)
    generate_voice()

    images = generate_images(topic)
    create_video(images)

    print("✅ final.mp4 created successfully")

if __name__ == "__main__":
    main()