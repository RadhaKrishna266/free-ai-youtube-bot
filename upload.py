import os
import sys
import subprocess
import requests
import textwrap
import math
from pathlib import Path

# ================== CONFIG ==================
TOPIC = os.getenv("TOPIC", "The mystery of Stonehenge")
VOICE = "en-IN-PrabhatNeural"
IMAGE_COUNT = 40          # capped for speed
VIDEO_SIZE = "1920x1080"
IMAGE_DURATION = 7        # seconds per image
WORKDIR = Path("work")
WORKDIR.mkdir(exist_ok=True)

# ================== SCRIPT ==================
def generate_script(topic):
    print("Generating long script...")
    paragraphs = []
    for i in range(1, 9):  # 8 sections ≈ 6–8 mins
        paragraphs.append(
            f"Section {i}. {topic}. "
            f"This part explains historical background, theories, evidence, "
            f"and expert opinions in a detailed and engaging way. "
            f"We explore facts, mysteries, and unanswered questions."
        )
    script = "\n\n".join(paragraphs)
    Path("script.txt").write_text(script, encoding="utf-8")
    return script

# ================== VOICE ==================
def generate_voice():
    print("Generating voice safely...")
    audio_parts = []
    text = Path("script.txt").read_text(encoding="utf-8")

    chunks = textwrap.wrap(text, 800)
    for i, chunk in enumerate(chunks):
        out = WORKDIR / f"voice_{i}.mp3"
        subprocess.run([
            "edge-tts",
            "--voice", VOICE,
            "--text", chunk,
            "--write-media", str(out)
        ], check=True)
        audio_parts.append(out)

    with open("audio_list.txt", "w") as f:
        for a in audio_parts:
            f.write(f"file '{a.resolve()}'\n")

    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", "audio_list.txt",
        "-c", "copy",
        "voice.mp3"
    ], check=True)

# ================== IMAGES ==================
def download_images(topic):
    print("Downloading topic images...")
    headers = {"User-Agent": "Mozilla/5.0"}
    images = []

    for i in range(IMAGE_COUNT):
        url = f"https://source.unsplash.com/1600x900/?{topic.replace(' ', ',')},{i}"
        img_path = WORKDIR / f"img_{i}.jpg"
        r = requests.get(url, headers=headers, timeout=20)
        img_path.write_bytes(r.content)
        images.append(img_path)

    return images

# ================== VIDEO ==================
def create_video(images):
    print("Creating animated video...")
    with open("images.txt", "w") as f:
        for img in images:
            f.write(f"file '{img.resolve()}'\n")
            f.write(f"duration {IMAGE_DURATION}\n")
        f.write(f"file '{images[-1].resolve()}'\n")

    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", "images.txt",
        "-vf",
        f"scale={VIDEO_SIZE},zoompan=z='min(zoom+0.0005,1.1)':d=125",
        "-pix_fmt", "yuv420p",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "video.mp4"
    ], check=True)

# ================== MERGE ==================
def merge_audio_video():
    print("Merging audio + video...")
    subprocess.run([
        "ffmpeg", "-y",
        "-i", "video.mp4",
        "-i", "voice.mp3",
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        "final_video.mp4"
    ], check=True)

# ================== MAIN ==================
def main():
    print("Starting auto video pipeline...")
    print("Topic:", TOPIC)

    generate_script(TOPIC)
    generate_voice()
    images = download_images(TOPIC)
    create_video(images)
    merge_audio_video()

    print("DONE ✅ final_video.mp4 ready")

if __name__ == "__main__":
    main()