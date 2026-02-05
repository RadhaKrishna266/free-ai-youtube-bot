import os
import subprocess
import requests
import asyncio
import edge_tts
import time
from pathlib import Path
from PIL import Image
from io import BytesIO

# ================= CONFIG =================
PIXABAY_KEY = os.getenv("PIXABAY_API_KEY")

IMAGE_QUERY = "Lord Krishna Vishnu cosmic divine illustration"
EXCLUDE_TERMS = [
    "shiva", "shankar", "mahadev",
    "goddess", "durga", "parvati", "lakshmi",
    "jesus", "christ", "church",
    "temple", "idol", "statue",
    "child", "baby", "kid"
]

FPS = "25"
START_IMAGE = "Image1.png"
SCRIPT_FILE = "script.txt"
TANPURA = "audio/tanpura.mp3"

MAX_IMAGES = 10
MAX_SCAN = 80              # max images to inspect
MAX_IMAGE_TIME = 300       # ⏱️ 5 minutes hard stop

Path("tts").mkdir(exist_ok=True)
Path("images").mkdir(exist_ok=True)
Path("clips").mkdir(exist_ok=True)

# ================= EPISODE =================
ep_file = Path("episode_number.txt")
EP = int(ep_file.read_text()) if ep_file.exists() else 1
ep_file.write_text(str(EP + 1))

# ================= UTILS =================
def run(cmd, cwd=None):
    subprocess.run(cmd, check=True, cwd=cwd)

async def tts(text, out):
    t = edge_tts.Communicate(text, "hi-IN-MadhurNeural")
    await t.save(out)

# ================= MAIN =================
async def main():
    print(f"🚀 Vishnu Purana – Episode {EP}")

    # ---------- SCRIPT ----------
    lines = [
        l.strip()
        for l in Path(SCRIPT_FILE).read_text(encoding="utf-8").splitlines()
        if l.strip()
    ]

    # ---------- TTS ----------
    audio = []

    await tts("सनातन ज्ञान धारा में आपका स्वागत है। आज हम विष्णु पुराण की कथा सुनेंगे।", "tts/start.mp3")
    audio.append("start.mp3")

    for i, line in enumerate(lines):
        f = f"n_{i:03}.mp3"
        await tts(line, f"tts/{f}")
        audio.append(f)

    await tts("यह था आज का विष्णु पुराण अध्याय। हरि ॐ।", "tts/end.mp3")
    audio.append("end.mp3")

    with open("tts/list.txt", "w") as f:
        for a in audio:
            f.write(f"file '{a}'\n")

    run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", "list.txt", "-c:a", "mp3", "voice_raw.mp3"
    ], cwd="tts")

    run([
        "ffmpeg", "-y",
        "-i", "tts/voice_raw.mp3",
        "-i", TANPURA,
        "-filter_complex", "[1:a]volume=0.035[a1];[0:a][a1]amix=inputs=2",
        "-c:a", "mp3",
        "voice.mp3"
    ])

    # ---------- IMAGE FETCH WITH HARD LIMIT ----------
    print("🖼️ Fetching Krishna/Vishnu images (time-limited)")

    start_time = time.time()
    saved = 0
    scanned = 0

    r = requests.get(
        "https://pixabay.com/api/",
        params={
            "key": PIXABAY_KEY,
            "q": IMAGE_QUERY,
            "image_type": "illustration",
            "orientation": "horizontal",
            "category": "religion",
            "safesearch": "true",
            "per_page": 80
        },
        timeout=15
    ).json()

    for h in r.get("hits", []):
        if saved >= MAX_IMAGES:
            break

        if scanned >= MAX_SCAN:
            print("⚠️ Max scan limit reached")
            break

        if time.time() - start_time > MAX_IMAGE_TIME:
            print("⏱️ Image fetch time limit reached")
            break

        scanned += 1
        tags = (h.get("tags", "") + h.get("user", "")).lower()

        if any(bad in tags for bad in EXCLUDE_TERMS):
            continue

        try:
            img_data = requests.get(h["largeImageURL"], timeout=10).content
            img = Image.open(BytesIO(img_data))
            img.verify()
            img = Image.open(BytesIO(img_data))

            w, hgt = img.size
            if w < 1200 or w < hgt:
                continue

            img.convert("RGB").save(f"images/{saved:03}.jpg", "JPEG", quality=95)
            saved += 1
            print(f"✅ Image {saved}/{MAX_IMAGES}")

        except Exception:
            continue

    if saved == 0:
        raise RuntimeError("❌ No valid Krishna/Vishnu images found")

    # ---------- VIDEO ----------
    def clip(img, out):
        run([
            "ffmpeg", "-y", "-loop", "1", "-i", img,
            "-t", "8",
            "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,"
                   "pad=1280:720:(ow-iw)/2:(oh-ih)/2",
            "-r", FPS, "-pix_fmt", "yuv420p", out
        ])

    clip(START_IMAGE, "clips/000.mp4")

    for i, img in enumerate(sorted(Path("images").glob("*.jpg")), start=1):
        clip(str(img), f"clips/{i:03}.mp4")

    with open("clips/list.txt", "w") as f:
        for c in sorted(Path("clips").glob("*.mp4")):
            f.write(f"file '{c.name}'\n")

    run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", "list.txt", "-i", "../voice.mp3",
        "-c:v", "copy", "-c:a", "aac", "-shortest",
        f"../final_video_episode_{EP}.mp4"
    ], cwd="clips")

    print("✅ FINAL VIDEO READY")

asyncio.run(main())