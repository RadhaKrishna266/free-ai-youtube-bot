import os
import subprocess
import requests
import asyncio
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import edge_tts
from bs4 import BeautifulSoup

# ---------------- CONFIG ----------------
SCRIPT_FILE = "script.txt"
IMAGE_DIR = "images"
AUDIO_DIR = "audio_blocks"
VIDEO_DIR = "video_blocks"
FINAL_VIDEO = "final_video.mp4"

TANPURA_FILE = "audio/tanpura.mp3"
PIXABAY_API_KEY = os.environ.get("PIXABAY_API_KEY")

BLOCKS = 5
PIXABAY_QUERY = "Lord Vishnu statue"

# ---------------- CREATE FOLDERS ----------------
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)

# ---------------- UTILS ----------------
def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)

def placeholder(path, text="ॐ नमो नारायणाय"):
    img = Image.new("RGB", (1280, 720), (10, 5, 0))
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 48)
    except:
        font = None
    d.text((60, 330), text, fill=(255, 215, 0), font=font)
    img.save(path)

# ---------------- WIKIMEDIA IMAGES ----------------
def fetch_commons_images(category, count):
    url = f"https://commons.wikimedia.org/wiki/Category:{category.replace(' ', '_')}"
    images = []

    try:
        html = requests.get(url, timeout=20).text
        soup = BeautifulSoup(html, "html.parser")

        for img in soup.select("img"):
            src = img.get("src")
            if src and src.startswith("//upload.wikimedia.org"):
                images.append("https:" + src)
            if len(images) >= count:
                break

    except Exception as e:
        print("⚠ Wikimedia error:", e)

    return images

# ---------------- PIXABAY FALLBACK ----------------
def fetch_pixabay_images(query, count):
    url = "https://pixabay.com/api/"
    params = {
        "key": PIXABAY_API_KEY,
        "q": query,
        "image_type": "photo",
        "orientation": "horizontal",
        "category": "religion",
        "editors_choice": "true",
        "safesearch": "true",
        "per_page": count * 3
    }

    try:
        res = requests.get(url, params=params, timeout=20).json()
        hits = res.get("hits", [])

        filtered = []
        for h in hits:
            tags = h.get("tags", "").lower()
            if any(k in tags for k in ["vishnu", "lakshmi", "narayan"]):
                filtered.append(h["largeImageURL"])

        return filtered[:count]

    except Exception as e:
        print("⚠ Pixabay error:", e)
        return []

# ---------------- DOWNLOAD IMAGES ----------------
def download_images(urls):
    paths = []

    for i, url in enumerate(urls):
        path = f"{IMAGE_DIR}/{i:03d}.jpg"
        try:
            r = requests.get(url, timeout=20)
            if r.status_code == 200:
                with open(path, "wb") as f:
                    f.write(r.content)
            else:
                placeholder(path)
        except:
            placeholder(path)

        paths.append(path)

    return paths

# ---------------- IMAGE PROCESS ----------------
def process_images(image_paths):
    processed = []

    for path in image_paths:
        img = Image.open(path).convert("RGB")
        img.thumbnail((1280, 720), Image.Resampling.LANCZOS)

        w, h = img.size
        w += w % 2
        h += h % 2

        bg = Image.new("RGB", (w, h), (0, 0, 0))
        bg.paste(img, ((w - img.width)//2, (h - img.height)//2))
        bg.save(path)

        processed.append(path)

    return processed

# ---------------- AUDIO ----------------
async def generate_single_audio(text, index):
    out = f"{AUDIO_DIR}/{index:03d}.mp3"
    voice = edge_tts.Communicate(text=text, voice="hi-IN-MadhurNeural")
    await voice.save(out)

def generate_audio(blocks):
    async def runner():
        for i, text in enumerate(blocks):
            if text.strip():
                await generate_single_audio(text, i)
    asyncio.run(runner())

# ---------------- VIDEO ----------------
def create_video(images, count):
    clips = []

    for i in range(count):
        img = images[i]
        aud = f"{AUDIO_DIR}/{i:03d}.mp3"
        clip = f"{VIDEO_DIR}/{i:03d}.mp4"

        if not os.path.exists(aud):
            print(f"⚠ Missing audio {aud}, skipping")
            continue

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", img,
            "-i", aud,
            "-i", TANPURA_FILE,
            "-filter_complex",
            "[2:a]volume=0.2[a2];[1:a][a2]amix=inputs=2:duration=first[a]",
            "-map", "0:v",
            "-map", "[a]",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-shortest",
            clip
        ]

        run(cmd)
        clips.append(clip)

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

    intro = (
        "नमस्कार। स्वागत है आप सभी का "
        "Sanatan Gyan Dhara चैनल पर। "
        "आज हम आपके लिए विष्णु पुराण का प्रथम अध्याय प्रस्तुत कर रहे हैं।"
    )

    outro = (
        "🙏 यदि आपको यह वीडियो पसंद आया हो, "
        "तो कृपया लाइक, शेयर और सब्सक्राइब अवश्य करें। "
        "Sanatan Gyan Dhara पर प्रतिदिन नया सनातन ज्ञान।"
    )

    blocks.insert(0, intro)
    blocks.append(outro)

    print("🌐 Fetching images from Wikimedia Commons...")
    urls = fetch_commons_images("Vishnu", BLOCKS)

    if len(urls) < BLOCKS:
        print("⚠ Wikimedia insufficient, using Pixabay...")
        urls += fetch_pixabay_images(PIXABAY_QUERY, BLOCKS - len(urls))

    image_files = process_images(download_images(urls))

    # 🔒 SYNC EVERYTHING
    final_count = min(len(blocks), len(image_files), BLOCKS)
    blocks = blocks[:final_count]
    image_files = image_files[:final_count]

    print(f"✅ Using {final_count} blocks")

    print("🔊 Generating audio...")
    generate_audio(blocks)

    print("🎬 Creating video...")
    create_video(image_files, final_count)

    print("✅ FINAL VIDEO READY:", FINAL_VIDEO)

if __name__ == "__main__":
    main()