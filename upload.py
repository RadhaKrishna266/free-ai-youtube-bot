import os
import requests
from urllib.parse import quote
from pathlib import Path
import subprocess
from time import sleep
from random import shuffle

# ---------------- CONFIG ----------------
PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY")  # Make sure secret is set
HF_API_KEY = os.getenv("HF_API_KEY")
BLOCKS = 5  # Number of video blocks to create
IMAGE_DIR = Path("images")
AUDIO_DIR = Path("audio")
AUDIO_BLOCKS_DIR = Path("audio_blocks")
VIDEO_DIR = Path("video_blocks")
TANPURA_AUDIO = AUDIO_DIR / "tanpura.mp3"
QUERY = "Vaikunth Vishnu Lakshmi Narayan"

# Create folders if not exist
for folder in [IMAGE_DIR, AUDIO_DIR, AUDIO_BLOCKS_DIR, VIDEO_DIR]:
    folder.mkdir(parents=True, exist_ok=True)


# ---------------- PIXABAY FETCH ----------------
def fetch_pixabay_images(query, num_images):
    print(f"🌐 Fetching images for query: {query}")
    url = f"https://pixabay.com/api/?key={PIXABAY_API_KEY}&q={quote(query)}&image_type=photo&orientation=horizontal&per_page={num_images}"
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        data = res.json()
    except Exception as e:
        print(f"⚠ Failed to fetch from Pixabay: {e}")
        return []
    
    images = []
    for hit in data.get("hits", []):
        img_url = hit.get("largeImageURL")
        if img_url and img_url not in images:
            images.append(img_url)
    return images


# ---------------- IMAGE DOWNLOAD ----------------
def download_images(urls):
    local_paths = []
    for i, url in enumerate(urls):
        ext = url.split(".")[-1].split("?")[0]
        path = IMAGE_DIR / f"{i:03d}.{ext}"
        try:
            r = requests.get(url, stream=True, timeout=10)
            if r.status_code == 200:
                with open(path, "wb") as f:
                    for chunk in r.iter_content(1024):
                        f.write(chunk)
                local_paths.append(path)
        except Exception as e:
            print(f"⚠ Failed to download {url}: {e}")
    return local_paths


# ---------------- HF AI GENERATION ----------------
def generate_ai_images(num):
    print("🤖 Generating AI fallback images...")
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    images = []
    for i in range(num):
        payload = {
            "inputs": QUERY,
            "options": {"wait_for_model": True}
        }
        try:
            r = requests.post("https://api-inference.huggingface.co/models/stable-diffusion-v1-5", headers=headers, json=payload, timeout=60)
            r.raise_for_status()
            img_data = r.content
            path = IMAGE_DIR / f"{i:03d}.png"
            with open(path, "wb") as f:
                f.write(img_data)
            images.append(path)
        except Exception as e:
            print(f"⚠ HF generation failed: {e}")
    return images


# ---------------- VIDEO CREATION ----------------
def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)


def create_video(images, audio_blocks, tanpura_audio):
    for i, img_path in enumerate(images):
        audio_block = audio_blocks[i]
        out_path = VIDEO_DIR / f"{i:03d}.mp4"
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(img_path),
            "-i", str(audio_block),
            "-i", str(tanpura_audio),
            "-filter_complex",
            "[2:a]volume=0.2[a2];[1:a][a2]amix=inputs=2:duration=first:dropout_transition=2[a]",
            "-map", "0:v", "-map", "[a]",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-shortest",
            str(out_path)
        ]
        run(cmd)


# ---------------- MAIN ----------------
def main():
    # 1️⃣ Try fetching images from Pixabay
    pixabay_urls = fetch_pixabay_images(QUERY, BLOCKS)
    images = download_images(pixabay_urls)
    
    # 2️⃣ If not enough, fallback to HF AI
    if len(images) < BLOCKS:
        needed = BLOCKS - len(images)
        images += generate_ai_images(needed)

    if len(images) < BLOCKS:
        raise Exception("❌ Not enough images to create video blocks")

    # 3️⃣ Get audio blocks
    audio_files = sorted(AUDIO_BLOCKS_DIR.glob("*.mp3"))
    if len(audio_files) < BLOCKS:
        raise Exception("❌ Not enough audio blocks")

    # 4️⃣ Shuffle to prevent repetition
    shuffle(images)
    shuffle(audio_files)

    # 5️⃣ Create video blocks
    create_video(images[:BLOCKS], audio_files[:BLOCKS], TANPURA_AUDIO)
    print("✅ Video blocks created successfully!")


if __name__ == "__main__":
    main()