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

START_IMAGE = "Image1.png"  # make sure this exists
SCRIPT_FILE = "script.txt"
EPISODE_NUMBER_FILE = "episode_number.txt"

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
        f"scale={VIDEO_SIZE}:force_original_aspect_ratio=decrease,"
        f"pad={VIDEO_SIZE}:(ow-iw)/2:(oh-ih)/2:color=black",
        "-r", FPS,
        "-pix_fmt", "yuv420p",
        out
    ])

def get_episode_number():
    if Path(EPISODE_NUMBER_FILE).exists():
        num = int(Path(EPISODE_NUMBER_FILE).read_text().strip())
    else:
        num = 1
    Path(EPISODE_NUMBER_FILE).write_text(str(num + 1))
    return num

# ================= MAIN =================
async def main():
    episode_number = get_episode_number()
    print(f"🚀 Vishnu Purana Daily Bot Started - Episode {episode_number}")

    # ---------- READ STORY ----------
    story = Path(SCRIPT_FILE).read_text(encoding="utf-8").strip().split("\n")
    story = [s.strip() for s in story if s.strip()]

    # ---------- TTS ----------
    await tts("सनातन ज्ञान धारा में आपका स्वागत है। आज हम विष्णु पुराण की कथा प्रारंभ कर रहे हैं।", "tts/start.mp3")
    audio_files = ["tts/start.mp3"]

    for i, line in enumerate(story):
        f = f"tts/n_{i:03}.mp3"
        await tts(line, f)
        audio_files.append(f)

    await tts("यह था आज का विष्णु पुराण अध्याय। अगले भाग में पुनः मिलेंगे। हरि ॐ।", "tts/end.mp3")
    audio_files.append("tts/end.mp3")

    # ---------- AUDIO CONCAT ----------
    with open("tts/list.txt", "w", encoding="utf-8") as f:
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
    if not Path(START_IMAGE).exists():
        raise FileNotFoundError(f"{START_IMAGE} NOT FOUND in repo")

    fetch_images()

    # ---------- VIDEO CLIPS ----------
    duration = 8
    clips = []

    make_clip(START_IMAGE, duration, "clips/000.mp4")
    clips.append("000.mp4")

    imgs = sorted(Path("images").glob("*.jpg"))
    for i, img in enumerate(imgs, start=1):
        out = f"{i:03}.mp4"
        make_clip(str(img), duration, f"clips/{out}")
        clips.append(out)

    # ---------- CONCAT VIDEO (RE-ENCODE) ----------
    with open("clips/list.txt", "w", encoding="utf-8") as f:
        for c in clips:
            f.write(f"file '{Path('clips') / c}'\n")

    run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", "clips/list.txt",
        "-i", "voice.mp3",
        "-c:v", "libx264",      # re-encode video
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "aac",
        "-shortest",
        f"final_video_episode_{episode_number}.mp4"
    ])

    print(f"✅ FINAL VIDEO CREATED: final_video_episode_{episode_number}.mp4")

# ================= RUN =================
if __name__ == "__main__":
    asyncio.run(main())