import os
import subprocess
import requests
import asyncio
import edge_tts
from pathlib import Path

# ================= CONFIG =================
PIXABAY_KEY = os.getenv("PIXABAY_API_KEY")

# STRICT FILTER — ONLY KRISHNA / VISHNU
IMAGE_QUERY = "Lord Krishna Vishnu illustration"
FPS = "25"

START_IMAGE = "Image1.png"
SCRIPT_FILE = "script.txt"
TANPURA = "audio/tanpura.mp3"

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
    t = edge_tts.Communicate(
        text=text,
        voice="hi-IN-MadhurNeural",
        rate="+0%",
        pitch="+0Hz"
    )
    await t.save(out)
    print(f"▶ TTS saved: {out}")

# ================= MAIN =================
async def main():
    print(f"🚀 Vishnu Purana Daily – Episode {EP}")

    # ---------- READ FULL SCRIPT ----------
    story = Path(SCRIPT_FILE).read_text(encoding="utf-8")
    lines = [l.strip() for l in story.splitlines() if l.strip()]

    # ---------- TTS ----------
    audio_files = []

    await tts(
        "सनातन ज्ञान धारा में आपका स्वागत है। आज हम विष्णु पुराण की पवित्र कथा का श्रवण करेंगे।",
        "tts/start.mp3"
    )
    audio_files.append("start.mp3")

    for i, line in enumerate(lines):
        name = f"n_{i:03}.mp3"
        await tts(line, f"tts/{name}")
        audio_files.append(name)

    await tts(
        "यह था आज का विष्णु पुराण अध्याय। अगले भाग में पुनः मिलेंगे। हरि ॐ।",
        "tts/end.mp3"
    )
    audio_files.append("end.mp3")

    # ---------- CONCAT VOICE ----------
    with open("tts/list.txt", "w") as f:
        for a in audio_files:
            f.write(f"file '{a}'\n")

    run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", "list.txt",
        "-c:a", "mp3",
        "-b:a", "192k",
        "voice_raw.mp3"
    ], cwd="tts")

    # ---------- MIX TANPURA (LOW VOLUME) ----------
    run([
        "ffmpeg", "-y",
        "-i", "tts/voice_raw.mp3",
        "-i", TANPURA,
        "-filter_complex",
        "[1:a]volume=0.04[a1];[0:a][a1]amix=inputs=2:dropout_transition=2",
        "-c:a", "mp3",
        "voice.mp3"
    ])

    # ---------- IMAGE CHECK ----------
    if not Path(START_IMAGE).exists():
        raise FileNotFoundError("Image1.png NOT FOUND")

    # ---------- PIXABAY (STRICT FILTER) ----------
    print("▶ Fetching Krishna/Vishnu images only")
    r = requests.get(
        "https://pixabay.com/api/",
        params={
            "key": PIXABAY_KEY,
            "q": IMAGE_QUERY,
            "image_type": "illustration",
            "category": "religion",
            "safesearch": "true",
            "per_page": 12
        }
    ).json()

    for i, h in enumerate(r.get("hits", [])):
        img = requests.get(h["largeImageURL"]).content
        Path(f"images/{i:03}.jpg").write_bytes(img)

    # ---------- VIDEO CLIPS (NO CROP) ----------
    def clip(img, out):
        run([
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", img,
            "-t", "8",
            "-vf",
            "scale=1280:720:force_original_aspect_ratio=decrease,"
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

    # ---------- FINAL VIDEO ----------
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