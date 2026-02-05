import os
import asyncio
import subprocess
from PIL import Image, ImageDraw, ImageFont
import edge_tts

SCRIPT = "script.txt"
IMAGE = "Image1.png"
AUDIO = "voice.mp3"
VIDEO = "final_video.mp4"

VOICE = "hi-IN-MadhurNeural"


# ---------------- CREATE SAFE IMAGE ----------------
def rebuild_image():
    print("🖼 Rebuilding Image1.png safely")

    img = Image.new("RGB", (1280, 720), (10, 10, 10))
    draw = ImageDraw.Draw(img)

    text = "विष्णु पुराण\nसनातन ज्ञान"
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 80)
    except:
        font = ImageFont.load_default()

    w, h = draw.multiline_textsize(text, font=font)
    draw.multiline_text(
        ((1280 - w) / 2, (720 - h) / 2),
        text,
        fill=(255, 215, 0),
        font=font,
        align="center"
    )

    img.save(IMAGE, "PNG")
    print("✅ Image rebuilt successfully")


# ---------------- TTS ----------------
async def generate_audio():
    if not os.path.exists(SCRIPT):
        raise FileNotFoundError("script.txt missing")

    text = open(SCRIPT, "r", encoding="utf-8").read().strip()
    if not text:
        raise ValueError("script.txt empty")

    print("🔊 Generating audio")
    tts = edge_tts.Communicate(text, VOICE)
    await tts.save(AUDIO)
    print("✅ Audio done")


# ---------------- VIDEO ----------------
def create_video():
    print("🎥 Creating video")

    subprocess.run([
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", IMAGE,
        "-i", AUDIO,
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-tune", "stillimage",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-shortest",
        VIDEO
    ], check=True)

    print("✅ Video created:", VIDEO)


# ---------------- MAIN ----------------
async def main():
    rebuild_image()
    await generate_audio()
    create_video()


if __name__ == "__main__":
    asyncio.run(main())