import os
import requests
import subprocess
import asyncio
from pathlib import Path
import edge_tts

# ===================== CONFIG =====================
IMAGE_DIR = "images"
CLIP_DIR = "clips"
TTS_DIR = "tts"

SCRIPT_FILE = "script.txt"
OUTPUT_VIDEO = "final_video.mp4"

START_IMAGE = "Image1.png"          # EXACT filename from repo
BACKGROUND_MUSIC = "tanpura.mp3"    # Must exist in repo root

PIXABAY_KEY = os.environ.get("PIXABAY_API_KEY")
PIXABAY_API = "https://pixabay.com/api/"

os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(CLIP_DIR, exist_ok=True)
os.makedirs(TTS_DIR, exist_ok=True)

# ===================== UTILS =====================
def log(msg):
    print(f"▶ {msg}")

def run(cmd):
    subprocess.run(cmd, check=True)

def fetch_pixabay_images(query, count=8):
    log(f"Fetching images for '{query}' from Pixabay...")
    r = requests.get(
        PIXABAY_API,
        params={
            "key": PIXABAY_KEY,
            "q": query,
            "image_type": "photo",
            "per_page": count,
            "safesearch": "true"
        },
        timeout=20
    ).json()

    paths = []
    for i, hit in enumerate(r.get("hits", [])):
        url = hit["largeImageURL"]
        path = f"{IMAGE_DIR}/{i:03d}.jpg"
        img = requests.get(url, timeout=20).content
        with open(path, "wb") as f:
            f.write(img)
        paths.append(path)
        log(f"✅ Image saved: {path}")
    return paths

async def tts(text, out_file):
    voice = "hi-IN-SwaraNeural"
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(out_file)
    log(f"✅ TTS saved: {out_file}")

def make_clip(image, duration, out):
    run([
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", image,
        "-t", str(duration),
        "-vf",
        "scale=1280:720:force_original_aspect_ratio=decrease,"
        "pad=1280:720:(ow-iw)/2:(oh-ih)/2",
        "-pix_fmt", "yuv420p",
        out
    ])

# ===================== MAIN =====================
async def main():
    log("🚀 Vishnu Purana Daily Bot Started")

    # ---------- READ SCRIPT ----------
    with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]

    # ---------- TTS ----------
    tts_files = []

    start_text = (
        "सनातन ज्ञान धारा में आपका हार्दिक स्वागत है। "
        "आज हम प्रारंभ कर रहे हैं विष्णु पुराण की पावन कथा।"
    )
    await tts(start_text, f"{TTS_DIR}/start.mp3")
    tts_files.append(f"{TTS_DIR}/start.mp3")

    for i, line in enumerate(lines):
        out = f"{TTS_DIR}/n_{i:03d}.mp3"
        await tts(line, out)
        tts_files.append(out)

    end_text = (
        "आज के विष्णु पुराण अध्याय का यहीं समापन होता है। "
        "कल फिर मिलेंगे एक नए अध्याय के साथ। हरि ओम।"
    )
    await tts(end_text, f"{TTS_DIR}/end.mp3")
    tts_files.append(f"{TTS_DIR}/end.mp3")

    # ---------- COMBINE VOICE ----------
    with open("voice_list.txt", "w") as f:
        for t in tts_files:
            f.write(f"file '{t}'\n")

    run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", "voice_list.txt",
        "-c", "copy",
        "voice.mp3"
    ])

    # ---------- MIX TANPURA (FIXED) ----------
    run([
        "ffmpeg", "-y",
        "-stream_loop", "-1",
        "-i", BACKGROUND_MUSIC,
        "-i", "voice.mp3",
        "-filter_complex",
        "amix=inputs=2:weights=1|0.3:dropout_transition=2",
        "-shortest",
        "-c:a", "mp3",
        "final_audio.mp3"
    ])

    # ---------- IMAGES ----------
    images = fetch_pixabay_images("lord vishnu painting", 8)

    if Path(START_IMAGE).exists():
        images.insert(0, START_IMAGE)
    else:
        raise FileNotFoundError("❌ Image1.png NOT FOUND")

    # ---------- VIDEO CLIPS ----------
    total_duration = float(subprocess.check_output([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=nokey=1:noprint_wrappers=1",
        "final_audio.mp3"
    ]))

    per_image = max(total_duration / len(images), 4)

    clips = []
    for i, img in enumerate(images):
        clip = f"{CLIP_DIR}/clip_{i:03d}.mp4"
        make_clip(img, per_image, clip)
        clips.append(clip)

    with open("clips.txt", "w") as f:
        for c in clips:
            f.write(f"file '{c}'\n")

    # ---------- FINAL VIDEO ----------
    run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", "clips.txt",
        "-i", "final_audio.mp3",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-pix_fmt", "yuv420p",
        OUTPUT_VIDEO
    ])

    log(f"✅ FINAL VIDEO CREATED: {OUTPUT_VIDEO}")

# =====================
if __name__ == "__main__":
    asyncio.run(main())