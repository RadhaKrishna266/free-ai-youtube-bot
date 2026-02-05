import os
import subprocess
import asyncio
import edge_tts
from pathlib import Path

# ================= CONFIG =================
SCRIPT_FILE = "script.txt"
IMAGE_FILE = "Image1.png"

BELL = "audio/temple_bell.mp3"
TANPURA = "audio/tanpura.mp3"

FPS = "25"

Path("tts").mkdir(exist_ok=True)

# ================= UTILS =================
def run(cmd, timeout=300, cwd=None):
    subprocess.run(cmd, check=True, timeout=timeout, cwd=cwd)

async def tts(text, out):
    speaker = edge_tts.Communicate(
        text=text,
        voice="hi-IN-MadhurNeural",
        rate="+0%",
        pitch="+0Hz"
    )
    await speaker.save(out)

# ================= MAIN =================
async def main():
    print("🔔 Starting devotional audiobook")

    if not Path(SCRIPT_FILE).exists():
        raise FileNotFoundError("script.txt not found")

    if not Path(IMAGE_FILE).exists():
        raise FileNotFoundError("Image1.png not found")

    # ---------- READ SCRIPT ----------
    text = Path(SCRIPT_FILE).read_text(encoding="utf-8").strip()

    print("🗣 Generating narration...")
    await tts(text, "tts/narration.mp3")

    # ---------- ADD BELL AT START ----------
    print("🔔 Adding bell sound...")
    run([
        "ffmpeg", "-y",
        "-i", BELL,
        "-i", "tts/narration.mp3",
        "-filter_complex",
        "[0:a]atrim=0:3,afade=t=out:st=2:d=1[b];"
        "[b][1:a]concat=n=2:v=0:a=1",
        "-c:a", "mp3",
        "tts/voice_with_bell.mp3"
    ], timeout=120)

    # ---------- MIX TANPURA ----------
    print("🎶 Mixing tanpura background...")
    run([
        "ffmpeg", "-y",
        "-i", "tts/voice_with_bell.mp3",
        "-i", TANPURA,
        "-filter_complex",
        "[1:a]volume=0.03[a1];[0:a][a1]amix=inputs=2:duration=first",
        "-c:a", "mp3",
        "voice.mp3"
    ], timeout=180)

    # ---------- FINAL VIDEO (SINGLE IMAGE) ----------
    print("🎬 Rendering final video...")
    run([
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", IMAGE_FILE,
        "-i", "voice.mp3",
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-vf", "scale=1280:720",
        "-r", FPS,
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-shortest",
        "final_video.mp4"
    ], timeout=300)

    print("✅ FINAL VIDEO READY: final_video.mp4")

# ================= RUN =================
asyncio.run(main())