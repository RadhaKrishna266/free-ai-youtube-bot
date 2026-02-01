import os
import requests
import shutil
from pathlib import Path
import subprocess

# ================= CONFIG =================
BLOCKS = 5  # Number of images/audio blocks you want
PIXABAY_KEY = os.environ.get("PIXABAY_API_KEY")  # Use your GitHub secret
QUERY = "Vaikunth Vishnu Lakshmi Narayan"
TANPURA_AUDIO = "audio/tanpura.mp3"  # Background tanpura
IMAGES_DIR = Path("images")
AUDIO_BLOCKS_DIR = Path("audio_blocks")
VIDEO_BLOCKS_DIR = Path("video_blocks")

# Create directories if not exist
IMAGES_DIR.mkdir(parents=True, exist_ok=True)
VIDEO_BLOCKS_DIR.mkdir(parents=True, exist_ok=True)

# ================= FUNCTIONS =================
def fetch_pixabay_images(query, count):
    print(f"🌐 Fetching images for query: {query}")
    url = f"https://pixabay.com/api/?key={PIXABAY_KEY}&q={query}&image_type=photo&orientation=horizontal&per_page={count}&safesearch=true"
    res = requests.get(url)
    if res.status_code != 200:
        raise Exception(f"⚠ Failed to fetch from Pixabay: {res.status_code} {res.text}")
    data = res.json()
    hits = data.get("hits", [])
    if len(hits) < count:
        raise Exception("❌ Not enough images to create video blocks")
    urls = [hit["largeImageURL"] for hit in hits[:count]]
    return urls

def download_images(urls):
    print("🖼 Downloading images...")
    for idx, url in enumerate(urls):
        resp = requests.get(url, stream=True)
        if resp.status_code == 200:
            with open(IMAGES_DIR / f"{idx:03d}.jpg", "wb") as f:
                resp.raw.decode_content = True
                shutil.copyfileobj(resp.raw, f)
        else:
            raise Exception(f"⚠ Failed to download image: {url}")

def run(cmd):
    print(f"▶ Running command: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

def create_video(blocks):
    print("🎬 Creating video...")
    for idx in range(blocks):
        img = IMAGES_DIR / f"{idx:03d}.jpg"
        audio_block = AUDIO_BLOCKS_DIR / f"{idx:03d}.mp3"
        out_video = VIDEO_BLOCKS_DIR / f"{idx:03d}.mp4"
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(img),
            "-i", str(audio_block),
            "-i", TANPURA_AUDIO,
            "-filter_complex",
            "[2:a]volume=0.2[a2];[1:a][a2]amix=inputs=2:duration=first:dropout_transition=2[a]",
            "-map", "0:v",
            "-map", "[a]",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-shortest",
            str(out_video)
        ]
        run(cmd)

# ================= MAIN =================
def main():
    urls = fetch_pixabay_images(QUERY, BLOCKS)
    download_images(urls)
    create_video(BLOCKS)
    print("✅ All video blocks created successfully!")

if __name__ == "__main__":
    main()