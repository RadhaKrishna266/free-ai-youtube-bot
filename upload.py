import os
import requests
import subprocess
import asyncio
import edge_tts
from pathlib import Path

# ================= CONFIG =================
IMAGE_DIR = "images"
CLIP_DIR = "clips"
TTS_DIR = "tts"

SCRIPT_FILE = "script.txt"
OUTPUT_VIDEO = "final_video.mp4"
BACKGROUND_MUSIC = "tanpura.mp3"

START_IMAGE = "Image1.png"   # <-- CASE MATCHES YOUR REPO
PIXABAY_API = "https://pixabay.com/api/"
PIXABAY_KEY = os.environ.get("PIXABAY_API_KEY")

VOICE = "hi-IN-SwaraNeural"

os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(CLIP_DIR, exist_ok=True)
os.makedirs(TTS_DIR, exist_ok=True)

# ================= UTILS =================
def run(cmd):
    subprocess.run(cmd, check=True)

def log(msg):
    print(f"▶ {msg}")

# ================= TTS =================
async def tts(text, out):
    c = edge_tts.Communicate(text, VOICE)
    await c.save(out)
    log(f"✅ TTS saved: {out}")

# ================= PIXABAY =================
def fetch_images(query, count=8):
    log("📸 Fetching Vishnu images from Pixabay...")
    r = requests.get(
        PIXABAY_API,
        params={"key": PIXABAY_KEY, "q": query, "image_type": "photo", "per_page": count},
        timeout=20
    ).json()

    paths = []
    for i, hit in enumerate(r.get("hits", [])):
        img = requests.get(hit["largeImageURL"], timeout=20).content
        p = f"{IMAGE_DIR}/{i:03d}.jpg"
        with open(p, "wb") as f:
            f.write(img)
        paths.append(p)
    return paths

# ================= VIDEO BLOCK =================
def make_clip(img, dur, out):
    run([
        "ffmpeg", "-y",
        "-loop", "1",
        "-framerate", "1",
        "-i", img,
        "-t", str(dur),
        "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:black",
        "-pix_fmt", "yuv420p",
        "-r", "24",
        out
    ])

# ================= MAIN =================
async def main():
    log("🚀 Vishnu Purana Daily Bot Started")

    # ---------- READ SCRIPT ----------
    lines = [l.strip() for l in open(SCRIPT_FILE, encoding="utf-8") if l.strip()]

    # ---------- START / END TEXT ----------
    start_text = (
        "सनातन ज्ञान धारा में आपका स्वागत है। "
        "आज हम आरंभ कर रहे हैं विष्णु पुराण की पावन कथा।"
    )

    end_text = (
        "आज के इस विष्णु पुराण अध्याय का यही समापन है। "
        "कल हम अगला अध्याय लेकर आएंगे। "
        "ॐ नमो नारायणाय।"
    )

    # ---------- TTS ----------
    tts_files = []

    await tts(start_text, f"{TTS_DIR}/start.mp3")
    tts_files.append(f"{TTS_DIR}/start.mp3")

    for i, line in enumerate(lines):
        out = f"{TTS_DIR}/n_{i:03d}.mp3"
        await tts(line, out)
        tts_files.append(out)

    await tts(end_text, f"{TTS_DIR}/end.mp3")
    tts_files.append(f"{TTS_DIR}/end.mp3")

    # ---------- MERGE VOICE ----------
    with open("voice_list.txt", "w") as f:
        for a in tts_files:
            f.write(f"file '{a}'\n")

    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0",
         "-i", "voice_list.txt", "-c", "copy", "voice.mp3"])

    # ---------- ADD TANPURA ----------
    run([
        "ffmpeg", "-y",
        "-i", "voice.mp3",
        "-i", BACKGROUND_MUSIC,
        "-filter_complex", "amix=inputs=2:weights=1 0.3",
        "-c:a", "mp3",
        "final_audio.mp3"
    ])

    # ---------- IMAGES ----------
    images = fetch_images("lord vishnu statue painting", 8)
    images = [START_IMAGE] + images + [images[-1]]  # end uses Vishnu image

    # ---------- DURATION ----------
    dur = float(subprocess.check_output([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=nokey=1:noprint_wrappers=1",
        "final_audio.mp3"
    ]))
    per = max(dur / len(images), 5)

    # ---------- CLIPS ----------
    clips = []
    for i, img in enumerate(images):
        c = f"{CLIP_DIR}/c_{i:03d}.mp4"
        make_clip(img, per, c)
        clips.append(c)

    with open("clips.txt", "w") as f:
        for c in clips:
            f.write(f"file '{c}'\n")

    # ---------- FINAL VIDEO ----------
    run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", "clips.txt",
        "-i", "final_audio.mp3",
        "-map", "0:v",
        "-map", "1:a",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-shortest",
        OUTPUT_VIDEO
    ])

    log("🎉 FINAL VIDEO CREATED SUCCESSFULLY")

if __name__ == "__main__":
    asyncio.run(main())