import os
import requests
import subprocess
import asyncio
from pathlib import Path
from PIL import Image
from edge_tts import Communicate

# ---------------- CONFIG ----------------
SCRIPT_FILE = "script.txt"
IMAGE_DIR = "images"
AUDIO_DIR = "audio_blocks"
VIDEO_DIR = "video_blocks"
FINAL_VIDEO = "final_video.mp4"
TANPURA_FILE = "audio/tanpura.mp3"  # Already in repo
BLOCKS = 5  # Number of video blocks
QUERY = "Vaikunth Vishnu Lakshmi Narayan"
PIXABAY_KEY = os.environ.get("PIXABAY_KEY")  # Optional: can skip if using placeholder

# ---------------- CREATE FOLDERS ----------------
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)

# ---------------- UTILS ----------------
def run(cmd):
    print("▶ Running command:", " ".join(cmd))
    subprocess.run(cmd, check=True)

def placeholder_image(path, text="ॐ नमो नारायणाय"):
    """Create a fallback placeholder image."""
    img = Image.new("RGB", (1280, 720), (0, 0, 0))
    img.save(path)

# ---------------- IMAGE FETCHING ----------------
def fetch_pixabay_images(query, count):
    """Fetch images from Pixabay. Fallback to placeholder if fails."""
    urls = []
    if PIXABAY_KEY:
        url = f"https://pixabay.com/api/?key={PIXABAY_KEY}&q={query}&image_type=photo&orientation=horizontal&per_page={count}&safesearch=true"
        res = requests.get(url)
        if res.status_code == 200:
            data = res.json()
            hits = data.get("hits", [])
            for i, h in enumerate(hits):
                if i >= count:
                    break
                urls.append(h["largeImageURL"])
        else:
            print(f"⚠ Pixabay API error {res.status_code}, using placeholders")
    # Fill placeholders if not enough images
    while len(urls) < count:
        urls.append(None)
    return urls

def download_images(urls):
    for i, url in enumerate(urls):
        out_path = f"{IMAGE_DIR}/{i:03d}.jpg"
        if url:
            try:
                r = requests.get(url, timeout=30)
                with open(out_path, "wb") as f:
                    f.write(r.content)
                continue
            except Exception as e:
                print("❌ Image download failed:", e)
        # fallback
        placeholder_image(out_path)

# ---------------- AUDIO GENERATION ----------------
async def generate_single_audio(text, index):
    out = f"{AUDIO_DIR}/{index:03d}.mp3"
    communicate = Communicate(text=text, voice="hi-IN-MadhurNeural")
    await communicate.save(out)

def generate_audio(blocks):
    async def runner():
        for i, text in enumerate(blocks):
            if text.strip():
                await generate_single_audio(text, i)
    asyncio.run(runner())

# ---------------- VIDEO CREATION ----------------
def create_video(num_blocks):
    clips = []
    for i in range(num_blocks):
        img = f"{IMAGE_DIR}/{i:03d}.jpg"
        aud = f"{AUDIO_DIR}/{i:03d}.mp3"
        clip = f"{VIDEO_DIR}/{i:03d}.mp4"
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", img,
            "-i", aud,
            "-i", TANPURA_FILE,
            "-filter_complex",
            "[2:a]volume=0.2[a2];[1:a][a2]amix=inputs=2:duration=first:dropout_transition=2[a]",
            "-map", "0:v",
            "-map", "[a]",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-shortest",
            clip
        ]
        run(cmd)
        clips.append(clip)

    # Concatenate all clips
    with open("list.txt", "w") as f:
        for c in clips:
            f.write(f"file '{c}'\n")
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
    # Split script into blocks
    blocks = Path(SCRIPT_FILE).read_text(encoding="utf-8").split("\n\n")
    intro = "नमस्कार। स्वागत है आप सभी का VishnuPriya श्रृंखला में।"
    outro = "\n\n🙏 अगर आपको यह वीडियो पसंद आया हो, तो कृपया लाइक, शेयर और सब्सक्राइब जरूर करें।"
    blocks.insert(0, intro)
    blocks.append(outro)

    blocks = blocks[:BLOCKS]  # Limit to BLOCKS
    print("🌐 Fetching images for query:", QUERY)
    urls = fetch_pixabay_images(QUERY, len(blocks))
    download_images(urls)

    print("🔊 Generating audio...")
    generate_audio(blocks)

    print("🎬 Creating video...")
    create_video(len(blocks))

    print("✅ FINAL VIDEO READY:", FINAL_VIDEO)

if __name__ == "__main__":
    main()