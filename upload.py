import os
import subprocess
import requests
import asyncio
from pathlib import Path
from PIL import Image, ImageFilter
import edge_tts
import random

# ================= CONFIG =================
SCRIPT_FILE = "script.txt"

IMAGE_DIR = "images"
AUDIO_DIR = "audio_blocks"
VIDEO_DIR = "video_blocks"

FINAL_VIDEO = "final_video.mp4"
TANPURA_FILE = "audio/tanpura.mp3"

PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")

TARGET_IMAGES = 6

PEXELS_QUERIES = [
    "lord vishnu painting illustration",
    "vaikuntha vishnu art",
    "lakshmi narayan painting",
    "lord krishna vishnu avatar art",
    "narayana devotional illustration",
    "hindu god digital art",
    "vishnu temple idol"
]

# ================= SETUP =================
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)

# ================= UTILS =================
def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)

# ================= IMAGE FETCH =================
def fetch_pexels_images():
    if not PEXELS_API_KEY:
        raise RuntimeError("PEXELS_API_KEY not set")

    headers = {"Authorization": PEXELS_API_KEY}
    collected = []

    for query in PEXELS_QUERIES:
        if len(collected) >= TARGET_IMAGES:
            break

        params = {
            "query": query,
            "per_page": 5,
            "orientation": "landscape"
        }

        try:
            r = requests.get(
                "https://api.pexels.com/v1/search",
                headers=headers,
                params=params,
                timeout=20
            )
            data = r.json()
            photos = data.get("photos", [])
            random.shuffle(photos)

            for p in photos:
                url = p["src"]["large"]
                if url not in collected:
                    collected.append(url)
                if len(collected) >= TARGET_IMAGES:
                    break

        except Exception as e:
            print("⚠ Pexels error:", e)

    return collected

def download_images(urls):
    paths = []
    for i, url in enumerate(urls):
        path = f"{IMAGE_DIR}/{i:03d}.jpg"
        r = requests.get(url, timeout=20)
        if r.status_code == 200:
            with open(path, "wb") as f:
                f.write(r.content)
            paths.append(path)
    return paths

# ================= IMAGE PROCESS (FULLSCREEN + BLUR) =================
def process_images(paths):
    final = []
    for p in paths:
        img = Image.open(p).convert("RGB")

        # background (blurred fill)
        bg = img.resize((1280, 720), Image.Resampling.LANCZOS)
        bg = bg.filter(ImageFilter.GaussianBlur(25))

        # foreground (fit)
        fg = img.copy()
        fg.thumbnail((1100, 620), Image.Resampling.LANCZOS)

        bg.paste(
            fg,
            ((1280 - fg.width) // 2, (720 - fg.height) // 2)
        )

        bg.save(p)
        final.append(p)

    return final

# ================= AUDIO =================
async def gen_audio(text, idx):
    out = f"{AUDIO_DIR}/{idx:03d}.mp3"
    tts = edge_tts.Communicate(
        text=text,
        voice="hi-IN-MadhurNeural"
    )
    await tts.save(out)

def generate_audio(blocks):
    async def runner():
        for i, t in enumerate(blocks):
            if t.strip():
                await gen_audio(t, i)
    asyncio.run(runner())

# ================= VIDEO (ZOOM EFFECT) =================
def create_video(images, blocks_count):
    clips = []

    for i in range(blocks_count):
        img = images[i]
        aud = f"{AUDIO_DIR}/{i:03d}.mp3"
        clip = f"{VIDEO_DIR}/{i:03d}.mp4"

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", img,
            "-i", aud,
            "-i", TANPURA_FILE,
            "-filter_complex",
            (
                "zoompan=z='min(zoom+0.0008,1.12)':d=125,"
                "scale=1280:720,"
                "[v];"
                "[2:a]volume=0.2[a2];"
                "[1:a][a2]amix=inputs=2:duration=first[a]"
            ),
            "-map", "[v]",
            "-map", "[a]",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
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

# ================= MAIN =================
def main():
    print("🌐 Fetching Vishnu devotional images...")
    urls = fetch_pexels_images()

    if not urls:
        raise RuntimeError("No images fetched from Pexels")

    images = process_images(download_images(urls))

    blocks = Path(SCRIPT_FILE).read_text(encoding="utf-8").split("\n\n")

    intro = (
        "नमस्कार। आप देख रहे हैं Sanatan Gyan Dhara। "
        "आज हम भगवान विष्णु के दिव्य स्वरूप, वैकुण्ठ धाम और उनके अवतारों के बारे में जानेंगे।"
    )
    outro = (
        "🙏 यदि यह वीडियो आपको पसंद आया हो, तो कृपया लाइक, शेयर और सब्सक्राइब करें। "
        "Sanatan Gyan Dhara के साथ जुड़े रहें।"
    )

    blocks = [intro] + blocks + [outro]
    final_count = min(len(images), len(blocks))

    print(f"✅ Using {final_count} blocks")

    generate_audio(blocks[:final_count])
    create_video(images[:final_count], final_count)

    print("🎉 FINAL VIDEO READY:", FINAL_VIDEO)

if __name__ == "__main__":
    main()