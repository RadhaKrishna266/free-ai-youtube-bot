import os
import subprocess
import requests
from pathlib import Path

SCRIPT_FILE = "script.txt"
IMAGE_DIR = "images"
AUDIO_DIR = "audio_blocks"
VIDEO_DIR = "video_blocks"
FINAL_VIDEO = "final_video.mp4"

PIXABAY_API_KEY = os.environ.get("PIXABAY_API_KEY")

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
    r = requests.get(
        "https://pixabay.com/api/",
        params={
            "key": PIXABAY_API_KEY,
            "q": "Hindu temple Krishna Vishnu devotional",
            "image_type": "photo",
            "orientation": "horizontal",
            "safesearch": "true",
            "per_page": 50,
        },
        timeout=30,
    ).json()

    hits = r.get("hits", [])
    if not hits:
        raise RuntimeError("Pixabay returned no images")

    for i in range(len(blocks)):
        img_url = hits[i % len(hits)]["largeImageURL"]
        img = requests.get(img_url, timeout=30).content
        with open(f"{IMAGE_DIR}/{i:03d}.jpg", "wb") as f:
            f.write(img)

# ---------------- AUDIO (EDGE-TTS HINDI) ----------------
def generate_audio(blocks):
    print("🎙 Generating NATURAL Hindi Neural voice...")
    for i, text in enumerate(blocks):
        text = text.strip()
        if not text:
            continue

        out = f"{AUDIO_DIR}/{i:03d}.wav"
        run([
            "python",
            "-m",
            "edge_tts",
            "--voice", "hi-IN-MadhurNeural",
            "--rate", "+0%",
            "--pitch", "+0Hz",
            "--text", text,
            "--write-media", out
        ])

# ---------------- VIDEO ----------------
def create_video(blocks):
    print("🎞 Creating video clips...")
    clips = []

    for i in range(len(blocks)):
        clip = f"{VIDEO_DIR}/{i:03d}.mp4"
        run([
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", f"{IMAGE_DIR}/{i:03d}.jpg",
            "-i", f"{AUDIO_DIR}/{i:03d}.wav",
            "-vf", "scale=1280:720,format=yuv420p",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-shortest",
            clip
        ])
        clips.append(clip)

    with open("list.txt", "w") as f:
        for c in clips:
            f.write(f"file '{c}'\n")

    print("🎬 Merging final video...")
    run([
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
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

    if os.path.exists(FINAL_VIDEO):
        print("✅ FINAL VIDEO READY:", os.path.abspath(FINAL_VIDEO))
    else:
        raise RuntimeError("❌ final_video.mp4 was NOT created")

if __name__ == "__main__":
    main()