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
TANPURA_FILE = "audio/tanpura.mp3"

W, H = 1280, 720

# ================= FOLDERS =================
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)

# ================= UTILS =================
def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)

# ================= IMAGE (NO TEXT – NEVER BLACK) =================
def create_vaikuntha_bg(out_path):
    base = Image.new("RGB", (W, H), "#070300")

    glow1 = Image.new("RGB", (W, H), "#2a1400")
    glow1 = glow1.filter(ImageFilter.GaussianBlur(120))

    glow2 = Image.new("RGB", (W, H), "#1b0c00")
    glow2 = glow2.filter(ImageFilter.GaussianBlur(200))

    img = Image.blend(base, glow1, 0.6)
    img = Image.blend(img, glow2, 0.4)

    img.save(out_path)

def prepare_images(blocks):
    for i in range(len(blocks)):
        out = f"{IMAGE_DIR}/{i:03d}.jpg"
        create_vaikuntha_bg(out)

# ================= AUDIO =================
async def gen_audio(text, idx):
    out = f"{AUDIO_DIR}/{idx:03d}.mp3"
    tts = edge_tts.Communicate(
        text=text,
        voice="hi-IN-MadhurNeural",
        rate="-5%"
    )
    await tts.save(out)

def generate_audio(blocks):
    async def runner():
        for i, t in enumerate(blocks):
            if t.strip():
                await gen_audio(t, i)
    asyncio.run(runner())

# ================= VIDEO =================
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
            # narration 100%, tanpura 20%
            "[2:a]volume=0.2[t];[1:a][t]amix=inputs=2:dropout_transition=2[a]",
            "-map", "0:v",
            "-map", "[a]",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
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

# ================= MAIN =================
def main():
    if not Path(SCRIPT_FILE).exists():
        raise FileNotFoundError("script.txt missing")

    if not Path(TANPURA_FILE).exists():
        raise FileNotFoundError("tanpura.mp3 missing")

    blocks = Path(SCRIPT_FILE).read_text(encoding="utf-8").split("\n\n")

    intro = "ॐ नमो नारायणाय। विष्णु पुराण की दिव्य कथा में आपका स्वागत है।"
    outro = "यदि यह कथा आपको प्रिय लगी हो, तो कृपया इसे साझा करें। ॐ नमो नारायणाय।"

    blocks.insert(0, intro)
    blocks.append(outro)

    prepare_images(blocks)
    generate_audio(blocks)
    create_video(blocks)

    print("✅ FINAL VIDEO READY:", FINAL_VIDEO)

if __name__ == "__main__":
    main()