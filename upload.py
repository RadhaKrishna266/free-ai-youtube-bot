import os
import subprocess
import asyncio
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
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

# ================= IMAGE CREATION =================
def create_divine_image(text, out_path):
    img = Image.new("RGB", (W, H), "#050200")

    # Background glow
    glow = Image.new("RGB", (W, H), "#1a0d00")
    glow = glow.filter(ImageFilter.GaussianBlur(120))
    img = Image.blend(img, glow, 0.6)

    draw = ImageDraw.Draw(img)

    # Font
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 52)
    except:
        font = ImageFont.load_default()

    # Text wrap
    lines = []
    words = text.split()
    line = ""
    for w in words:
        if len(line + w) < 26:
            line += w + " "
        else:
            lines.append(line)
            line = w + " "
    lines.append(line)

    y = H//2 - len(lines)*35
    for l in lines:
        draw.text(
            (W//2, y),
            l.strip(),
            fill=(255, 215, 140),
            font=font,
            anchor="mm"
        )
        y += 70

    img.save(out_path)

def prepare_images(blocks):
    for i, text in enumerate(blocks):
        out = f"{IMAGE_DIR}/{i:03d}.jpg"
        create_divine_image(text, out)

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
            "[1:a][2:a]amix=inputs=2:weights=2 0.5[a]",
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
    outro = "इस दिव्य ज्ञान को आगे बढ़ाएँ। Like, Share और Subscribe करें। ॐ नमो नारायणाय।"

    blocks.insert(0, intro)
    blocks.append(outro)

    prepare_images(blocks)
    generate_audio(blocks)
    create_video(blocks)

    print("✅ FINAL VIDEO READY:", FINAL_VIDEO)

if __name__ == "__main__":
    main()