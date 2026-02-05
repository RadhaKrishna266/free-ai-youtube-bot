import subprocess
import asyncio
import edge_tts
from pathlib import Path

# ================= CONFIG =================
SCRIPT_FILE = "script.txt"
IMAGE_FILE = "Image1.png"
BELL = "audio/bell.mp3"
TANPURA = "audio/tanpura.mp3"
FPS = "25"

Path("tts").mkdir(exist_ok=True)

# ================= SAFE RUN =================
def run(cmd, timeout=120):
    subprocess.run(cmd, check=True, timeout=timeout)

# ================= TTS =================
async def generate_tts(text, out):
    t = edge_tts.Communicate(
        text=text,
        voice="hi-IN-MadhurNeural",
        rate="+0%",
        pitch="+0Hz"
    )
    await t.save(out)

# ================= MAIN =================
async def main():
    print("🔔 Starting devotional audiobook")

    # ---------- READ SCRIPT ----------
    script = Path(SCRIPT_FILE).read_text(encoding="utf-8").strip()
    if not script:
        raise RuntimeError("❌ script.txt is empty")

    # ---------- TTS ----------
    print("🗣 Generating narration...")
    await generate_tts(script, "tts/narration.mp3")

    # ---------- BELL + NARRATION ----------
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
    ])

    # ---------- MIX TANPURA ----------
    print("🎵 Mixing tanpura...")
    run([
        "ffmpeg", "-y",
        "-i", "tts/voice_with_bell.mp3",
        "-i", TANPURA,
        "-filter_complex",
        "[1:a]volume=0.04[a1];[0:a][a1]amix=inputs=2",
        "-c:a", "mp3",
        "voice.mp3"
    ])

    # ---------- FINAL VIDEO ----------
    print("🎬 Rendering final video...")
    run([
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", IMAGE_FILE,
        "-i", "voice.mp3",
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-r", FPS,
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-shortest",
        "final_video.mp4"
    ], timeout=180)

    print("✅ DONE: final_video.mp4 created")

# ================= RUN =================
asyncio.run(main())