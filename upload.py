import os
import requests
import subprocess
from pathlib import Path
from urllib.parse import quote
import random
import time

# ================= CONFIG =================
PIXABAY_API_KEY = os.environ.get("PIXABAY_API_KEY")  # set in your repo secrets
HF_API_KEY = os.environ.get("HF_API_KEY")
BLOCKS = 5  # number of video blocks
TANPURA_AUDIO = "audio/tanpura.mp3"
QUERY_LIST = [
    "Vaikunth Vishnu",
    "Vishnu Avatars",
    "Lakshmi Narayan"
]

# ================= FOLDERS =================
IMAGES_DIR = Path("images")
VIDEO_DIR = Path("video_blocks")
AUDIO_BLOCKS_DIR = Path("audio_blocks")
IMAGES_DIR.mkdir(exist_ok=True)
VIDEO_DIR.mkdir(exist_ok=True)

# ================= PIXABAY FETCH =================
def fetch_pixabay_images(query, num_images):
    print(f"🌐 Fetching images for query: {query}")
    url = f"https://pixabay.com/api/?key={PIXABAY_API_KEY}&q={quote(query)}&image_type=photo&orientation=horizontal&per_page={num_images}"
    res = requests.get(url).json()
    images = []
    for hit in res.get("hits", []):
        img_url = hit.get("largeImageURL")
        if img_url and img_url not in images:
            images.append(img_url)
    return images

def download_image(url, path):
    try:
        r = requests.get(url, stream=True)
        if r.status_code == 200:
            with open(path, 'wb') as f:
                for chunk in r:
                    f.write(chunk)
            return True
    except:
        pass
    return False

# ================= HUGGINGFACE FALLBACK =================
def generate_ai_image(prompt, save_path):
    print(f"🤖 Generating AI image for missing block: {prompt}")
    HF_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2"
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    payload = {"inputs": prompt}
    response = requests.post(HF_URL, headers=headers, json=payload)
    if response.status_code == 200:
        with open(save_path, 'wb') as f:
            f.write(response.content)
        return True
    else:
        print("⚠ AI generation failed, retrying after 2s...")
        time.sleep(2)
        return generate_ai_image(prompt, save_path)

# ================= VIDEO CREATION =================
def run(cmd):
    subprocess.run(cmd, check=True)

def create_video(images, audio_blocks, tanpura_audio):
    for i, img_path in enumerate(images):
        audio_path = audio_blocks[i]
        out_path = VIDEO_DIR / f"{i:03}.mp4"
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", str(img_path),
            "-i", str(audio_path),
            "-i", str(tanpura_audio),
            "-filter_complex",
            "[2:a]volume=0.2[a2];[1:a][a2]amix=inputs=2:duration=first:dropout_transition=2[a]",
            "-map", "0:v", "-map", "[a]",
            "-c:v", "libx264", "-c:a", "aac", "-shortest",
            str(out_path)
        ]
        print(f"🎬 Creating video block {i+1}/{len(images)}...")
        run(cmd)

# ================= MAIN =================
def main():
    # Clear old images
    for f in IMAGES_DIR.glob("*"): f.unlink()
    images_urls = []
    
    # Fetch images from Pixabay
    for query in QUERY_LIST:
        urls = fetch_pixabay_images(query, BLOCKS)
        images_urls.extend(urls)
        if len(images_urls) >= BLOCKS:
            break
    images_urls = images_urls[:BLOCKS]
    
    # Download images or generate AI if missing
    images_paths = []
    for i in range(BLOCKS):
        img_file = IMAGES_DIR / f"{i:03}.jpg"
        if i < len(images_urls):
            success = download_image(images_urls[i], img_file)
            if not success:
                generate_ai_image(random.choice(QUERY_LIST), img_file)
        else:
            generate_ai_image(random.choice(QUERY_LIST), img_file)
        images_paths.append(img_file)

    # Ensure audio_blocks exist
    audio_files = sorted(list(AUDIO_BLOCKS_DIR.glob("*.mp3")))
    if len(audio_files) < BLOCKS:
        raise Exception(f"⚠ Not enough audio blocks! Found {len(audio_files)}, needed {BLOCKS}")

    # Create videos
    create_video(images_paths, audio_files, TANPURA_AUDIO)
    print("✅ Video blocks created successfully!")

if __name__ == "__main__":
    main()
