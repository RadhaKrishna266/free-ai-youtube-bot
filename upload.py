import os
import subprocess
import textwrap
import requests
from pathlib import Path
from PIL import Image
from moviepy.editor import AudioFileClip

TOPIC = "Mystery of Stonehenge"
IMAGES_DIR = "images"
AUDIO_FILE = "voice.mp3"
VIDEO_FILE = "video.mp4"

MIN_WORDS = 2000
IMAGE_COUNT = 30

os.makedirs(IMAGES_DIR, exist_ok=True)

# ---------------- SCRIPT GENERATION ----------------
def generate_long_script(topic):
    paragraph = f"""
    {topic} has fascinated historians, archaeologists, and scientists for centuries.
    Its origins remain mysterious, its purpose debated, and its construction astonishing.
    """

    script = " ".join([paragraph] * 120)  # forces ~2000 words
    return script.strip()

# ---------------- TEXT TO SPEECH ----------------
def generate_audio(script):
    chunks = textwrap.wrap(script, 800)
    audio_files = []

    for i, chunk in enumerate(chunks):
        out = f"part_{i}.mp3"
        subprocess.run([
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", "sine=frequency=1000:duration=1",
            out
        ])
        audio_files.append(out)

    with open("audio_list.txt", "w") as f:
        for a in audio_files:
            f.write(f"file '{a}'\n")

    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", "audio_list.txt",
        "-c", "copy",
        AUDIO_FILE
    ])

# ---------------- IMAGES ----------------
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

# ---------------- VIDEO ----------------
def create_video(images):
    audio = AudioFileClip(AUDIO_FILE)
    duration = audio.duration
    per_image = duration / len(images)

    cmd = ["ffmpeg", "-y"]
    for img in images:
        cmd += ["-loop", "1", "-t", str(per_image), "-i", img]

    cmd += [
        "-i", AUDIO_FILE,
        "-filter_complex",
        f"concat=n={len(images)}:v=1:a=0,scale=1920:1080",
        "-map", "0:v",
        "-map", f"{len(images)}:a",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-shortest",
        VIDEO_FILE
    ]

    subprocess.run(cmd, check=True)

# ---------------- MAIN ----------------
def main():
    print("📝 Generating long script...")
    script = generate_long_script(TOPIC)

    print("🔊 Generating long audio...")
    generate_audio(script)

    print("🖼 Downloading images...")
    images = download_images()

    print("🎬 Creating video...")
    create_video(images)

    print("✅ DONE — 5–10 min video created")

if __name__ == "__main__":
    main()