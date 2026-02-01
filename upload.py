import os
import requests
import subprocess
import asyncio
from pathlib import Path
from bs4 import BeautifulSoup
from PIL import Image
import edge_tts

# ---------------- CONFIG ----------------
GOOGLE_SEARCH_URL = "https://www.google.com/search?q=vaikunth+vishnu+vishnu+avtara+lakshmi+vishnh+animated+wallpapers+only+photos+without+text+high+resolution+only+clear+images+no+thumbnail+of+website+on+image&tbm=isch"
IMAGE_DIR = "images"
AUDIO_DIR = "audio_blocks"
VIDEO_DIR = "video_blocks"
FINAL_VIDEO = "final_video.mp4"
TANPURA_FILE = "audio/tanpura.mp3"
SCRIPT_FILE = "script.txt"
BLOCKS = 5  # number of segments

os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)

# ---------------- UTILS ----------------
def run(cmd):
    print("▶ Running command:", " ".join(cmd))
    subprocess.run(cmd, check=True)

# ---------------- FETCH GOOGLE IMAGES ----------------
def fetch_google_images(url, count=BLOCKS):
    print("🌐 Fetching high-res images from Google...")
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "lxml")

    # Google Images thumbnails store real URLs in 'data-src' or 'src'
    img_tags = soup.find_all("img")
    urls = []
    for img in img_tags:
        src = img.get("data-src") or img.get("src")
        if src and src.startswith("http"):
            if src not in urls:
                urls.append(src)
        if len(urls) >= count:
            break

    if len(urls) < count:
        raise Exception(f"❌ Not enough images found! Only {len(urls)} found")

    # Download images
    for i, u in enumerate(urls):
        path = f"{IMAGE_DIR}/{i:03d}.jpg"
        try:
            r = requests.get(u, stream=True, timeout=30)
            if r.status_code == 200:
                with open(path, "wb") as f:
                    for chunk in r.iter_content(1024):
                        f.write(chunk)
        except Exception as e:
            print("❌ Failed to download image:", e)
            Image.new("RGB", (1280, 720), (10, 5, 0)).save(path)

    print(f"✅ {len(urls)} images downloaded successfully")
    return [f"{IMAGE_DIR}/{i:03d}.jpg" for i in range(count)]

# ---------------- AUDIO GENERATION ----------------
async def generate_single_audio(text, index):
    out = f"{AUDIO_DIR}/{index:03d}.mp3"
    communicate = edge_tts.Communicate(text=text, voice="hi-IN-MadhurNeural")
    await communicate.save(out)

def generate_audio(blocks):
    async def runner():
        for i, text in enumerate(blocks):
            if text.strip():
                await generate_single_audio(text, i)
    asyncio.run(runner())
    print("✅ Audio blocks generated")

# ---------------- VIDEO CREATION ----------------
def create_video(image_files, audio_count):
    clips = []
    for i in range(audio_count):
        img = image_files[i]
        aud = f"{AUDIO_DIR}/{i:03d}.mp3"
        clip = f"{VIDEO_DIR}/{i:03d}.mp4"
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", img,
            "-i", aud,
            "-i", TANPURA_FILE,
            "-filter_complex", "[2:a]volume=0.2[a2];[1:a][a2]amix=inputs=2:duration=first:dropout_transition=2[a]",
            "-map", "0:v",
            "-map", "[a]",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-shortest", clip
        ]
        run(cmd)
        clips.append(clip)

    # Concatenate all clips
    with open("list.txt", "w") as f:
        for c in clips:
            f.write(f"file '{c}'\n")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "list.txt", "-c", "copy", FINAL_VIDEO])
    print("✅ Final video ready:", FINAL_VIDEO)

# ---------------- MAIN ----------------
def main():
    # Read script blocks
    blocks = Path(SCRIPT_FILE).read_text(encoding="utf-8").split("\n\n")
    intro = "नमस्कार। स्वागत है आप सभी का VishnuPriya श्रृंखला में।"
    outro = "🙏 अगर आपको यह वीडियो पसंद आया हो, तो कृपया लाइक, शेयर और सब्सक्राइब करें।"
    blocks.insert(0, intro)
    blocks.append(outro)

    # Fetch images
    image_files = fetch_google_images(GOOGLE_SEARCH_URL, len(blocks))

    # Generate audio
    generate_audio(blocks)

    # Create video
    create_video(image_files, len(blocks))

if __name__ == "__main__":
    main()