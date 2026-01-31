import os
import subprocess
import requests
import asyncio
from pathlib import Path
from hashlib import md5
import edge_tts

SCRIPT_FILE = "script.txt"
IMAGE_DIR = "images"
AUDIO_DIR = "audio_blocks"
VIDEO_DIR = "video_blocks"
FINAL_VIDEO = "final_video.mp4"

os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)

USED_IMAGES = set()

# ---------------- UTILS ----------------
def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)

# ---------------- WIKIMEDIA SEARCH ----------------
def wikimedia_search(query, limit=30):
    url = "https://commons.wikimedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": query,
        "gsrlimit": limit,
        "prop": "imageinfo",
        "iiprop": "url"
    }
    r = requests.get(url, params=params).json()
    pages = r.get("query", {}).get("pages", {})
    images = []
    for p in pages.values():
        info = p.get("imageinfo")
        if info:
            images.append(info[0]["url"])
    return images

# ---------------- DOWNLOAD IMAGES ----------------
def download_images(blocks):
    print("🖼 Downloading AUTHENTIC Vishnu Purana images (NO repeats)...")

    # FIRST IMAGE — VISHNU PURANA BOOK
    book_imgs = wikimedia_search("Vishnu Purana manuscript illustration", 10)
    if not book_imgs:
        raise RuntimeError("No Vishnu Purana manuscript found")

    first_img = book_imgs[0]
    save_image(first_img, 0)

    queries = [
        "Vishnu Vaikuntha painting",
        "Dashavatara Vishnu painting",
        "Vishnu cosmic form painting",
        "Vishnu temple mural",
        "Narayana Hindu painting"
    ]

    image_pool = []
    for q in queries:
        image_pool.extend(wikimedia_search(q, 40))

    if len(image_pool) < len(blocks):
        raise RuntimeError("Not enough Vishnu images")

    idx = 1
    for url in image_pool:
        if idx >= len(blocks):
            break
        if save_image(url, idx):
            idx += 1

    if idx < len(blocks):
        raise RuntimeError("Ran out of unique Vishnu images")

def save_image(url, index):
    h = md5(url.encode()).hexdigest()
    if h in USED_IMAGES:
        return False
    img = requests.get(url).content
    path = f"{IMAGE_DIR}/{index:03d}.jpg"
    with open(path, "wb") as f:
        f.write(img)
    USED_IMAGES.add(h)
    return True

# ---------------- AUDIO (EDGE-TTS) ----------------
async def speak(text, index):
    out = f"{AUDIO_DIR}/{index:03d}.wav"
    tts = edge_tts.Communicate(
        text=text,
        voice="hi-IN-MadhurNeural",
        rate="+0%",
        pitch="+0Hz"
    )
    await tts.save(out)

def generate_audio(blocks):
    print("🎙 Generating devotional Hindi voice...")
    async def runner():
        for i, t in enumerate(blocks):
            if t.strip():
                await speak(t, i)
    asyncio.run(runner())

# ---------------- VIDEO ----------------
def create_video(blocks):
    print("🎞 Rendering final Vishnu Purana episode...")

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
    print("✅ FIRST EPISODE READY:", FINAL_VIDEO)

if __name__ == "__main__":
    main()