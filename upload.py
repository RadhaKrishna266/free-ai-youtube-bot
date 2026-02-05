import os
import subprocess
import asyncio
import edge_tts
from pathlib import Path

# ================= CONFIG =================
IMAGE = "Image1.png"
SCRIPT_FILE = "script.txt"

BELL = "audio/temple_bell.mp3"
TANPURA = "audio/tanpura.mp3"

VOICE = "hi-IN-MadhurNeural"
FPS = "25"

MAX_FFMPEG_TIME = 300   # hard limit: 5 minutes per ffmpeg call

Path("tts").mkdir(exist_ok=True)

# ================= UTILS =================
def run(cmd, timeout=MAX_FFMPEG_TIME):
    subprocess.run(cmd, check=True, timeout=timeout)

async def tts(text, out):
    communicate = edge_tts.Communicate(
        text=text,
        voice=VOICE,
        rate="+0%",
        pitch="+0Hz"
    )
    await communicate.save(out)

# ================= MAIN =================
async def main():
    print("🔔 Starting devotional audiobook")

    # ---------- READ SCRIPT ----------
    script = Path(SCRIPT_FILE).read_text(encoding="utf-8").strip()
    if not script:
        raise RuntimeError("script.txt is empty")

    # ---------- TTS ----------
    print("🗣 Generating narration...")
    await tts(script, "tts/narration.mp3")

    # ---------- BELL + VOICE ----------
    print("🔔 Adding bell sound...")
    run([
        "ffmpeg", "-y",
        "-i", BELL,
        "-i", "tts/narration.mp3",
        "-filter_complex",
        "[0:a]atrim=0:3,afade=t=out:st=2:d=1[b];[b][1:a]concat=n=2:v=0:a=1",
        "-c:a", "mp3",
        "tts/voice_with_bell.mp3"
    ])

    # ---------- ADD TANPURA ----------
    print("🎶 Mixing tanpura...")
    run([
        "ffmpeg", "-y",
        "-i", "tts/voice_with_bell.mp3",
        "-i", TANPURA,
        "-filter_complex",
        "[1:a]volume=0.03[a1];[0:a][a1]amix=inputs=2:dropout_transition=2",
        "-c:a", "mp3",
        "tts/final_audio.mp3"
    ])

    # ---------- FINAL VIDEO ----------
    print("🎥 Creating static-image video...")
    run([
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", IMAGE,
        "-i", "tts/final_audio.mp3",
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-vf", "scale=1280:720",
        "-r", FPS,
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-shortest",
        "final_video.mp4"
    ], timeout=600)

    print("✅ FINAL VIDEO READY: final_video.mp4")

# ================= RUN =================
asyncio.run(main())