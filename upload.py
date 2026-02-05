import os
import subprocess
import asyncio
import edge_tts
from pathlib import Path

# ================= CONFIG =================
FPS = 25
START_IMAGE = "Image1.png"
SCRIPT_FILE = "script.txt"
TANPURA = "audio/tanpura.mp3"
MAX_VIDEO_SECONDS = 900  # 15 minutes hard cap

VOICE = "hi-IN-MadhurNeural"

Path("tts").mkdir(exist_ok=True)

# ================= EPISODE NUMBER =================
ep_file = Path("episode_number.txt")
EP = int(ep_file.read_text()) if ep_file.exists() else 1
ep_file.write_text(str(EP + 1))

# ================= UTILS =================
def run(cmd):
    subprocess.run(cmd, check=True)

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
    print(f"🚀 Vishnu Purana Audio Episode {EP}")

    if not Path(START_IMAGE).exists():
        raise FileNotFoundError("❌ Image1.png NOT FOUND")

    # ---------- READ SCRIPT (3 SHLOK ONLY) ----------
    lines = Path(SCRIPT_FILE).read_text(encoding="utf-8").splitlines()
    lines = [l.strip() for l in lines if l.strip()]

    if len(lines) == 0:
        raise RuntimeError("❌ script.txt is empty")

    # ---------- TTS ----------
    audio_files = []

    await tts(
        "सनातन ज्ञान धारा में आपका स्वागत है। आज हम विष्णु पुराण के तीन पवित्र श्लोकों का पाठ, अर्थ और भावार्थ सुनेंगे।",
        "tts/start.mp3"
    )
    audio_files.append("start.mp3")

    for i, line in enumerate(lines):
        name = f"n_{i:02}.mp3"
        await tts(line, f"tts/{name}")
        audio_files.append(name)

    await tts(
        "यह था आज का विष्णु पुराण पाठ। अगले अध्याय में पुनः मिलेंगे। हरि ॐ।",
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
        "-i", "tts/list.txt",
        "-c:a", "mp3",
        "-b:a", "192k",
        "voice_raw.mp3"
    ])

    # ---------- MIX TANPURA (LOW) ----------
    run([
        "ffmpeg", "-y",
        "-i", "voice_raw.mp3",
        "-i", TANPURA,
        "-filter_complex",
        "[1:a]volume=0.035[a1];[0:a][a1]amix=inputs=2",
        "-c:a", "mp3",
        "voice.mp3"
    ])

    # ---------- CREATE VIDEO FROM SINGLE IMAGE ----------
    run([
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", START_IMAGE,
        "-i", "voice.mp3",
        "-t", str(MAX_VIDEO_SECONDS),
        "-vf",
        "scale=1280:720:force_original_aspect_ratio=decrease,"
        "pad=1280:720:(ow-iw)/2:(oh-ih)/2",
        "-r", str(FPS),
        "-pix_fmt", "yuv420p",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-shortest",
        f"final_video_episode_{EP}.mp4"
    ])

    print(f"✅ FINAL VIDEO READY: final_video_episode_{EP}.mp4")

# ================= RUN =================
asyncio.run(main())