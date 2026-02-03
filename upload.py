import os
import subprocess
import requests
import asyncio
import edge_tts
from pathlib import Path

# ================= CONFIG =================
PIXABAY_KEY = os.getenv("PIXABAY_API_KEY")
IMAGE_QUERY = "Vishnu Krishna"
VIDEO_SIZE = "1280:720"
FPS = "25"

SCRIPT_FILE = "script.txt"

# find start image (case-insensitive)
start_image_candidates = list(Path(".").glob("Image*.png")) + list(Path(".").glob("image*.png"))
if not start_image_candidates:
    raise FileNotFoundError("No start image found in repo (expected Image1.png or image1.png)")
START_IMAGE = str(start_image_candidates[0])
print(f"▶ Using start image: {START_IMAGE}")

# folders
Path("tts").mkdir(exist_ok=True)
Path("images").mkdir(exist_ok=True)
Path("clips").mkdir(exist_ok=True)

# ================= HELPERS =================
def run(cmd, cwd=None):
    subprocess.run(cmd, check=True, cwd=cwd)

async def tts(text, out):
    communicate = edge_tts.Communicate(text, "hi-IN-MadhurNeural")
    await communicate.save(out)
    print(f"▶ TTS saved: {out}")

def fetch_images():
    print("▶ Fetching images from Pixabay...")
    url = "https://pixabay.com/api/"
    params = {
        "key": PIXABAY_KEY,
        "q": IMAGE_QUERY,
        "image_type": "photo",
        "safesearch": "true",
        "per_page": 12
    }
    r = requests.get(url, params=params).json()
    for i, hit in enumerate(r.get("hits", [])):
        img = requests.get(hit["largeImageURL"]).content
        with open(f"images/{i:03}.jpg", "wb") as f:
            f.write(img)

def make_clip(img, duration, out):
    run([
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", img,
        "-t", str(duration),
        "-vf",
        "scale=1280:720:force_original_aspect_ratio=decrease,"
        "pad=1280:720:(ow-iw)/2:(oh-ih)/2:color=black",
        "-r", FPS,
        "-pix_fmt", "yuv420p",
        out
    ])

# ================= MAIN =================
async def main():
    # Daily episode numbering from environment or default
    EPISODE = os.getenv("DAILY_EPISODE", "1")
    print(f"🚀 Vishnu Purana Daily Bot Started - Episode {EPISODE}")

    # ---------- READ STORY ----------
    story = Path(SCRIPT_FILE).read_text(encoding="utf-8").strip().split("\n")
    story = [s.strip() for s in story if s.strip()]

    # ---------- TTS ----------
    await tts(f"सनातन ज्ञान धारा में आपका स्वागत है। आज हम विष्णु पुराण की कथा प्रारंभ कर रहे हैं। यह एपिसोड संख्या {EPISODE} है।", "tts/start.mp3")
    audio_files = ["tts/start.mp3"]

    for i, line in enumerate(story):
        f = f"tts/n_{i:03}.mp3"
        await tts(line, f)
        audio_files.append(f)

    await tts("यह था आज का विष्णु पुराण अध्याय। अगले भाग में पुनः मिलेंगे। हरि ॐ।", "tts/end.mp3")
    audio_files.append("tts/end.mp3")

    # ---------- AUDIO CONCAT ----------
    with open("tts/list.txt", "w") as f:
        for a in audio_files:
            f.write(f"file '{a}'\n")

    run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", "tts/list.txt",
        "-c", "copy",
        "voice.mp3"
    ])

    # ---------- IMAGES ----------
    fetch_images()

    # ---------- VIDEO CLIPS ----------
    duration = 8
    clips = []

    # Start image clip
    make_clip(START_IMAGE, duration, "clips/000.mp4")
    clips.append("000.mp4")

    imgs = sorted(Path("images").glob("*.jpg"))
    for i, img in enumerate(imgs, start=1):
        out = f"{i:03}.mp4"
        make_clip(str(img), duration, f"clips/{out}")
        clips.append(out)

    # ---------- CONCAT VIDEO ----------
    with open("clips/list.txt", "w") as f:
        for c in clips:
            f.write(f"file '{c}'\n")

    run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", "list.txt",
        "-i", "../voice.mp3",
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        f"../final_video_episode_{EPISODE}.mp4"
    ], cwd="clips")

    print(f"✅ FINAL VIDEO CREATED: final_video_episode_{EPISODE}.mp4")

# ================= RUN =================
if __name__ == "__main__":
    asyncio.run(main())