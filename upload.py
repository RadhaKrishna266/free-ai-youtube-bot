import os
import subprocess
import asyncio
import edge_tts

IMAGE = "Image1.png"
SCRIPT = "script.txt"
AUDIO = "voice.mp3"
VIDEO = "final_video.mp4"

VOICE = "hi-IN-MadhurNeural"   # Hindi male (clear & calm)

# ---------------- IMAGE FIX ----------------
def fix_image():
    if not os.path.exists(IMAGE):
        raise FileNotFoundError("❌ Image1.png not found")

    print("🛠 Fixing Image1.png (FFmpeg-safe)")
    subprocess.run([
        "ffmpeg", "-y",
        "-i", IMAGE,
        "-vf", "scale=1280:720",
        IMAGE
    ], check=True)
    print("✅ Image fixed")

# ---------------- TTS ----------------
async def generate_audio():
    if not os.path.exists(SCRIPT):
        raise FileNotFoundError("❌ script.txt not found")

    text = open(SCRIPT, "r", encoding="utf-8").read().strip()
    if not text:
        raise ValueError("❌ script.txt is empty")

    print("🔊 Generating Hindi narration audio")
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(AUDIO)
    print("✅ Audio generated")

# ---------------- VIDEO ----------------
def create_video():
    print("🎥 Creating video (single image + audio)")
    subprocess.run([
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", IMAGE,
        "-i", AUDIO,
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-tune", "stillimage",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        VIDEO
    ], check=True)
    print("✅ Video created:", VIDEO)

# ---------------- MAIN ----------------
async def main():
    fix_image()
    await generate_audio()
    create_video()

if __name__ == "__main__":
    asyncio.run(main())