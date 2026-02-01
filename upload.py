import os
import subprocess
import asyncio
from pathlib import Path
from PIL import Image, ImageFilter
import edge_tts

# ================= CONFIG =================
SCRIPT_FILE = "script.txt"

IMAGE_DIR = "images"
AUDIO_DIR = "audio_blocks"
VIDEO_DIR = "video_blocks"

FINAL_VIDEO = "final_video.mp4"
TANPURA_FILE = "audio/tanpura.mp3"  # must exist

W, H = 1280, 720

VOICE = "hi-IN-MadhurNeural"

# =========================================

os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)


def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)


# ---------- BRIGHT VAIKUNTHA BACKGROUND ----------
def create_vaikuntha_bg(out_path):
    # Bright base (NOT black)
    base = Image.new("RGB", (W, H), (60, 30, 10))

    glow1 = Image.new("RGB", (W, H), (255, 190, 90))
    glow1 = glow1.filter(ImageFilter.GaussianBlur(260))

    glow2 = Image.new("RGB", (W, H), (160, 90, 20))
    glow2 = glow2.filter(ImageFilter.GaussianBlur(180))

    img = Image.blend(base, glow1, 0.35)
    img = Image.blend(img, glow2, 0.45)

    # Force brightness (YouTube-safe)
    img = img.point(lambda p: min(255, int(p * 1.3)))

    img.save(out_path, quality=95)


# ---------- IMAGES ----------
def prepare_images(blocks):
    for i in range(len(blocks)):
        out = f"{IMAGE_DIR}/{i:03d}.jpg"
        create_vaikuntha_bg(out)


# ---------- AUDIO ----------
async def generate_audio_block(text, index):
    out = f"{AUDIO_DIR}/{index:03d}.mp3"
    tts = edge_tts.Communicate(text=text, voice=VOICE)
    await tts.save(out)


def generate_audio(blocks):
    async def runner():
        for i, text in enumerate(blocks):
            if text.strip():
                await generate_audio_block(text, i)

    asyncio.run(runner())


# ---------- VIDEO ----------
def create_video(blocks):
    clips = []

    for i in range(len(blocks)):
        img = f"{IMAGE_DIR}/{i:03d}.jpg"
        aud = f"{AUDIO_DIR}/{i:03d}.mp3"
        out = f"{VIDEO_DIR}/{i:03d}.mp4"

        run([
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", img,
            "-i", aud,
            "-i", TANPURA_FILE,
            "-filter_complex",
            # narration + soft tanpura
            "[1:a][2:a]amix=inputs=2:weights=1 0.15:duration=first[a]",
            "-map", "0:v",
            "-map", "[a]",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-shortest",
            out
        ])

        clips.append(out)

    with open("list.txt", "w") as f:
        for c in clips:
            f.write(f"file '{c}'\n")

    run([
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", "list.txt",
        "-c", "copy",
        FINAL_VIDEO
    ])


# ---------- MAIN ----------
def main():
    if not Path(SCRIPT_FILE).exists():
        raise FileNotFoundError("❌ script.txt not found")

    if not Path(TANPURA_FILE).exists():
        raise FileNotFoundError("❌ tanpura.mp3 not found in audio/")

    blocks = Path(SCRIPT_FILE).read_text(encoding="utf-8").split("\n\n")

    intro = (
        "नमस्कार। आप सभी का स्वागत है। "
        "आज हम विष्णु पुराण की दिव्य कथा आरंभ कर रहे हैं।"
    )

    outro = (
        "🙏 यदि यह कथा आपको प्रिय लगी हो, "
        "तो कृपया लाइक, शेयर और सब्सक्राइब अवश्य करें।"
    )

    blocks.insert(0, intro)
    blocks.append(outro)

    prepare_images(blocks)
    generate_audio(blocks)
    create_video(blocks)

    print("✅ FINAL VIDEO CREATED:", FINAL_VIDEO)


if __name__ == "__main__":
    main()