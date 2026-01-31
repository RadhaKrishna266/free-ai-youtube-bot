import os
import subprocess
import requests
from pathlib import Path

SCRIPT_FILE = "script.txt"
IMAGE_DIR = "images"
AUDIO_DIR = "audio_blocks"
VIDEO_DIR = "video_blocks"
FINAL_VIDEO = "final_video.mp4"

PIXABAY_API_KEY = os.environ["PIXABAY_API_KEY"]

os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)

# ---------------- UTILS ----------------
def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)

# ---------------- IMAGES ----------------
def download_images(blocks):
    print("🖼 Downloading devotional images...")
    for i in range(len(blocks)):
        query = "Lord Vishnu Krishna Hindu devotional art"
        r = requests.get(
            "https://pixabay.com/api/",
            params={
                "key": PIXABAY_API_KEY,
                "q": query,
                "image_type": "photo",
                "orientation": "horizontal",
                "safesearch": "true",
                "per_page": 5
            }
        ).json()

        hits = r.get("hits", [])
        if hits:
            img = requests.get(hits[i % len(hits)]["largeImageURL"]).content
            with open(f"{IMAGE_DIR}/{i:03d}.jpg", "wb") as f:
                f.write(img)
        else:
            raise RuntimeError("Pixabay returned zero images — check API key")

# ---------------- AUDIO (HINDI – EDGE TTS) ----------------
def generate_audio(blocks):
    print("🎙 Generating CLEAR Hindi audio (Edge TTS)...")

    for i, text in enumerate(blocks):
        if not text.strip():
            continue

        out = f"{AUDIO_DIR}/{i:03d}.wav"
        run([
            "edge-tts",
            "--voice", "hi-IN-MadhurNeural",
            "--text", text,
            "--write-media", out
        ])

# ---------------- VIDEO ----------------
def create_video(blocks):
    print("🎞 Creating video...")
    clips = []

    for i in range(len(blocks)):
        audio = f"{AUDIO_DIR}/{i:03d}.wav"
        image = f"{IMAGE_DIR}/{i:03d}.jpg"
        clip = f"{VIDEO_DIR}/{i:03d}.mp4"

        run([
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", image,
            "-i", audio,
            "-t", "8",
            "-vf", "scale=1280:720,format=yuv420p",
            "-c:v", "libx264",
            "-c:a", "aac",
            clip
        ])
        clips.append(clip)

    with open("list.txt", "w") as f:
        for c in clips:
            f.write(f"file '{c}'\n")

    run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", "list.txt",
        "-c", "copy",
        FINAL_VIDEO
    ])

# ---------------- MAIN ----------------
def main():
    blocks = Path(SCRIPT_FILE).read_text(encoding="utf-8").split("\n\n")
    download_images(blocks)
    generate_audio(blocks)
    create_video(blocks)
    print("✅ FINAL VIDEO READY:", FINAL_VIDEO)

if __name__ == "__main__":
    main()