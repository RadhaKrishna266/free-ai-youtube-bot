import os
import subprocess
import requests
import asyncio
import edge_tts
from pathlib import Path

# ================= CONFIG =================
PIXABAY_KEY = os.getenv("PIXABAY_API_KEY")
IMAGE_QUERY = "Vishnu Krishna"
FPS = "25"

START_IMAGE = "image1.png"
SCRIPT_FILE = "script.txt"

Path("tts").mkdir(exist_ok=True)
Path("images").mkdir(exist_ok=True)
Path("clips").mkdir(exist_ok=True)

# ================= EPISODE NUMBER =================
ep_file = Path("episode_number.txt")
EP = int(ep_file.read_text()) if ep_file.exists() else 1
ep_file.write_text(str(EP + 1))

# ================= UTILS =================
def run(cmd, cwd=None):
    subprocess.run(cmd, check=True, cwd=cwd)

async def tts(text, out):
    t = edge_tts.Communicate(text, "hi-IN-MadhurNeural")
    await t.save(out)
    print(f"▶ TTS saved: {out}")

# ================= MAIN =================
async def main():
    print(f"🚀 Vishnu Purana Daily – Episode {EP}")

    story = Path(SCRIPT_FILE).read_text(encoding="utf-8").splitlines()
    story = [s.strip() for s in story if s.strip()]

    # ---------- TTS ----------
    await tts(
        "सनातन ज्ञान धारा में आपका स्वागत है। आज हम विष्णु पुराण की कथा प्रारंभ कर रहे हैं।",
        "tts/start.mp3"
    )

    audio = ["start.mp3"]

    for i, line in enumerate(story):
        name = f"n_{i:03}.mp3"
        await tts(line, f"tts/{name}")
        audio.append(name)

    await tts(
        "यह था आज का विष्णु पुराण अध्याय। अगले भाग में पुनः मिलेंगे। हरि ॐ।",
        "tts/end.mp3"
    )
    audio.append("end.mp3")

    # ---------- AUDIO CONCAT (FIXED FOREVER) ----------
    with open("tts/list.txt", "w") as f:
        for a in audio:
            f.write(f"file '{a}'\n")

    run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", "list.txt",
        "-c:a", "mp3",
        "-b:a", "192k",
        "voice.mp3"
    ], cwd="tts")

    run(["mv", "tts/voice.mp3", "voice.mp3"])

    # ---------- IMAGE CHECK ----------
    if not Path(START_IMAGE).exists():
        raise FileNotFoundError("image1.png NOT FOUND")

    # ---------- PIXABAY ----------
    print("▶ Fetching images from Pixabay")
    r = requests.get(
        "https://pixabay.com/api/",
        params={
            "key": PIXABAY_KEY,
            "q": IMAGE_QUERY,
            "image_type": "photo",
            "safesearch": "true",
            "per_page": 10
        }
    ).json()

    for i, h in enumerate(r["hits"]):
        img = requests.get(h["largeImageURL"]).content
        Path(f"images/{i:03}.jpg").write_bytes(img)

    # ---------- VIDEO CLIPS ----------
    def clip(img, out):
        run([
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", img,
            "-t", "8",
            "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,"
                   "pad=1280:720:(ow-iw)/2:(oh-ih)/2",
            "-r", FPS,
            "-pix_fmt", "yuv420p",
            out
        ])

    clip(START_IMAGE, "clips/000.mp4")

    imgs = sorted(Path("images").glob("*.jpg"))
    for i, img in enumerate(imgs, start=1):
        clip(str(img), f"clips/{i:03}.mp4")

    with open("clips/list.txt", "w") as f:
        for c in sorted(Path("clips").glob("*.mp4")):
            f.write(f"file '{c.name}'\n")

    run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", "list.txt",
        "-i", "../voice.mp3",
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        f"../final_video_episode_{EP}.mp4"
    ], cwd="clips")

    print(f"✅ FINAL VIDEO READY: final_video_episode_{EP}.mp4")

# ================= RUN =================
asyncio.run(main())