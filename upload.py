import os
import subprocess
import asyncio
import requests
from pathlib import Path
from bs4 import BeautifulSoup
import edge_tts

# ---------------- CONFIG ----------------
SCRIPT_FILE = "script.txt"
IMAGE_DIR = "images"
AUDIO_DIR = "audio_blocks"
VIDEO_DIR = "video_blocks"
FINAL_VIDEO = "final_video.mp4"
TANPURA_FILE = "audio/tanpura.mp3"
HF_API_KEY = os.environ.get("HF_API_KEY")  # Not used for images here
GOOGLE_IMAGES_URL = "https://www.google.com/search?q=vaikunth+vishnu+vishnu+avtara+lakshmi+vishnh+animated+wallpapers+only+photos+without+text&tbm=isch"

# ---------------- CREATE FOLDERS ----------------
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)

# ---------------- UTILS ----------------
def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)

# ---------------- IMAGE SCRAPER ----------------
def fetch_google_images(url, max_images=50):
    print(f"🖼 Fetching images from Google...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    r = requests.get(url, headers=headers, timeout=20)
    soup = BeautifulSoup(r.text, "html.parser")
    images = []
    for img in soup.find_all("img"):
        src = img.get("src")
        if src and src.startswith("http") and "gstatic.com" not in src:
            images.append(src)
        if len(images) >= max_images:
            break
    print(f"✅ Found {len(images)} images")
    return images

def download_images(blocks):
    urls = fetch_google_images(GOOGLE_IMAGES_URL, max_images=len(blocks))
    if not urls:
        raise RuntimeError("❌ No images found from Google!")
    used_urls = set()
    for i, _ in enumerate(blocks):
        path = f"{IMAGE_DIR}/{i:03d}.jpg"
        # Ensure no repeats
        for url in urls:
            if url not in used_urls:
                used_urls.add(url)
                try:
                    data = requests.get(url, timeout=15).content
                    with open(path, "wb") as f:
                        f.write(data)
                    break
                except:
                    continue

# ---------------- AUDIO GENERATION ----------------
async def generate_single_audio(text, index):
    out = f"{AUDIO_DIR}/{index:03d}.mp3"
    communicate = edge_tts.Communicate(
        text=text,
        voice="hi-IN-MadhurNeural"
    )
    await communicate.save(out)

def generate_audio(blocks):
    async def runner():
        for i, text in enumerate(blocks):
            if text.strip():
                await generate_single_audio(text, i)
    asyncio.run(runner())

# ---------------- VIDEO CREATION ----------------
def create_video(blocks):
    clips = []
    for i in range(len(blocks)):
        img = f"{IMAGE_DIR}/{i:03d}.jpg"
        aud = f"{AUDIO_DIR}/{i:03d}.mp3"
        clip = f"{VIDEO_DIR}/{i:03d}.mp4"
        run([
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
        ])
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
    blocks = Path(SCRIPT_FILE).read_text(encoding="utf-8").split("\n\n")
    intro = "नमस्कार। स्वागत है आप सभी का VishnuPriya श्रृंखला में। आज हम आपके लिए Vishnu Purana का पहला एपिसोड लाए हैं।"
    outro = "\n\n🙏 अगर आपको यह वीडियो पसंद आया हो, तो कृपया लाइक, शेयर और सब्सक्राइब जरूर करें। हर दिन एक नया एपिसोड आएगा।"
    blocks.insert(0, intro)
    blocks.append(outro)

    download_images(blocks)
    generate_audio(blocks)
    create_video(blocks)
    print("✅ FINAL VIDEO READY:", FINAL_VIDEO)

if __name__ == "__main__":
    main()