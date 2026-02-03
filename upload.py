import os
import requests
import subprocess
import asyncio
import edge_tts
from pathlib import Path

# ===================== CONFIG =====================
IMAGE_DIR = "images"
CLIP_DIR = "clips"
TTS_DIR = "tts"

SCRIPT_FILE = "script.txt"
OUTPUT_VIDEO = "final_video.mp4"
BACKGROUND_MUSIC = "tanpura.mp3"

START_IMAGE = "image1.png"   # MUST exist in repo
PIXABAY_API = "https://pixabay.com/api/"
PIXABAY_KEY = os.environ.get("PIXABAY_API_KEY")

VOICE = "hi-IN-SwaraNeural"

# =================================================

os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(CLIP_DIR, exist_ok=True)
os.makedirs(TTS_DIR, exist_ok=True)

def log(msg):
    print(f"▶ {msg}")

def run(cmd):
    subprocess.run(cmd, check=True)

# ===================== PIXABAY =====================
def fetch_pixabay_images(query, count=10):
    log(f"Fetching images from Pixabay: {query}")
    res = requests.get(
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
    for i, hit in enumerate(res.get("hits", [])):
        img_url = hit["largeImageURL"]
        path = f"{IMAGE_DIR}/{i:03d}.jpg"
        img = requests.get(img_url, timeout=20).content
        with open(path, "wb") as f:
            f.write(img)
        paths.append(path)
        log(f"Image saved: {path}")

    return paths

# ===================== TTS =====================
async def tts(text, outfile):
    t = edge_tts.Communicate(text, VOICE)
    await t.save(outfile)
    log(f"TTS saved: {outfile}")

# ===================== VIDEO BLOCK =====================
def make_clip(image, duration, out):
    run([
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", image,
        "-t", str(duration),
        "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:black",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        out
    ])

# ===================== MAIN =====================
async def main():
    log("🚀 Vishnu Purana Daily Bot Started")

    # ---------- Read Script ----------
    with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]

    # ---------- Start / End Narration ----------
    start_text = (
        "सनातन ज्ञान धारा में आपका स्वागत है। "
        "आज हम आरंभ कर रहे हैं विष्णु पुराण की दिव्य कथा।"
    )

    end_text = (
        "आज के विष्णु पुराण अध्याय का पाठ यहीं समाप्त होता है। "
        "कल फिर मिलेंगे एक नए अध्याय के साथ। "
        "जय श्री विष्णु।"
    )

    tts_files = []

    await tts(start_text, f"{TTS_DIR}/start.mp3")
    tts_files.append(f"{TTS_DIR}/start.mp3")

    for i, line in enumerate(lines):
        out = f"{TTS_DIR}/n_{i:03d}.mp3"
        await tts(line, out)
        tts_files.append(out)

    await tts(end_text, f"{TTS_DIR}/end.mp3")
    tts_files.append(f"{TTS_DIR}/end.mp3")

    # ---------- Combine Voice ----------
    with open("voice_list.txt", "w", encoding="utf-8") as f:
        for a in tts_files:
            f.write(f"file '{a}'\n")

    run([
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", "voice_list.txt",
        "-c", "copy",
        "voice.mp3"
    ])

    # ---------- Mix Tanpura ----------
    run([
        "ffmpeg", "-y",
        "-stream_loop", "-1",
        "-i", BACKGROUND_MUSIC,
        "-i", "voice.mp3",
        "-filter_complex",
        "[0:a]volume=0.3[a0];[a0][1:a]amix=inputs=2:dropout_transition=2",
        "-shortest",
        "-c:a", "mp3",
        "final_audio.mp3"
    ])

    # ---------- Images ----------
    images = []

    if Path(START_IMAGE).exists():
        images.append(START_IMAGE)
    else:
        raise FileNotFoundError("image1.png NOT FOUND in repo")

    images += fetch_pixabay_images("lord vishnu purana painting", 12)

    # ---------- Duration ----------
    dur = float(subprocess.check_output([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        "final_audio.mp3"
    ]).strip())

    per_img = max(dur / len(images), 4)

    clips = []
    for i, img in enumerate(images):
        clip = f"{CLIP_DIR}/c_{i:03d}.mp4"
        make_clip(img, per_img, clip)
        clips.append(clip)

    with open("clips.txt", "w") as f:
        for c in clips:
            f.write(f"file '{c}'\n")

    # ---------- Final Video ----------
    run([
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", "clips.txt",
        "-i", "final_audio.mp3",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-shortest",
        OUTPUT_VIDEO
    ])

    log("✅ FINAL VIDEO CREATED SUCCESSFULLY")

# ===================== RUN =====================
if __name__ == "__main__":
    asyncio.run(main())