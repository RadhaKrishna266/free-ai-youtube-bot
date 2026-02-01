import os
import subprocess
import requests
import asyncio
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import edge_tts

# ================= CONFIG =================
SCRIPT_FILE = "script.txt"
IMAGE_DIR = "images"
AUDIO_DIR = "audio_blocks"
VIDEO_DIR = "video_blocks"
FINAL_VIDEO = "final_video.mp4"
TANPURA_FILE = "audio/tanpura.mp3"

WIDTH = 1280
HEIGHT = 720

# ================= CREATE FOLDERS =================
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)

# ================= UTILS =================
def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)

def placeholder(path, text="ॐ नमो नारायणाय"):
    img = Image.new("RGB", (WIDTH, HEIGHT), (15, 5, 0))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 60)
    except:
        font = None
    draw.text((100, HEIGHT//2 - 40), text, fill=(255, 215, 0), font=font)
    img.save(path)

# ================= IMAGE GENERATION =================
def generate_ai_image(prompt, out_path):
    print(f"🖼 Generating image: {prompt[:60]}")

    safe_prompt = prompt.replace(" ", "%20")
    url = (
        f"https://image.pollinations.ai/prompt/"
        f"{safe_prompt},%20lord%20vishnu,%20vaikuntha,%20divine,%20hindu%20art"
        f"?width={WIDTH}&height={HEIGHT}&model=flux&seed=42"
    )

    try:
        r = requests.get(url, timeout=60)
        with open(out_path, "wb") as f:
            f.write(r.content)

        img = Image.open(out_path).convert("RGB")
        if img.getextrema() == ((0,0),(0,0),(0,0)):
            raise ValueError("Black image")

    except Exception as e:
        print("❌ Image failed, using placeholder:", e)
        placeholder(out_path)

def prepare_images(blocks):
    for i, text in enumerate(blocks):
        out = f"{IMAGE_DIR}/{i:03d}.jpg"
        prompt = f"Divine Vaikuntha scene, Lord Vishnu, celestial background, glowing, spiritual art, {text[:120]}"
        generate_ai_image(prompt, out)

# ================= AUDIO GENERATION =================
async def generate_audio_block(text, index):
    out = f"{AUDIO_DIR}/{index:03d}.mp3"
    communicate = edge_tts.Communicate(
        text=text,
        voice="hi-IN-MadhurNeural",
        rate="-5%"
    )
    await communicate.save(out)

def generate_audio(blocks):
    async def runner():
        for i, text in enumerate(blocks):
            if text.strip():
                await generate_audio_block(text, i)
    asyncio.run(runner())

# ================= VIDEO CREATION =================
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
            "[1:a][2:a]amix=inputs=2:weights=2 0.6[a]",
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

# ================= MAIN =================
def main():
    if not Path(SCRIPT_FILE).exists():
        raise FileNotFoundError("❌ script.txt not found")

    if not Path(TANPURA_FILE).exists():
        raise FileNotFoundError("❌ audio/tanpura.mp3 not found")

    blocks = Path(SCRIPT_FILE).read_text(encoding="utf-8").split("\n\n")

    intro = (
        "ॐ नमो नारायणाय।\n"
        "Sanatan Gyan Dhara में आपका स्वागत है।\n"
        "यह विष्णु पुराण की दिव्य श्रृंखला का प्रथम अध्याय है।"
    )

    outro = (
        "यदि आपको यह दिव्य ज्ञान प्रिय लगा हो,\n"
        "तो कृपया Like, Share और Subscribe करें।\n"
        "हम प्रतिदिन विष्णु पुराण का एक नया अध्याय प्रस्तुत करेंगे।\n"
        "ॐ नमो नारायणाय।"
    )

    blocks.insert(0, intro)
    blocks.append(outro)

    prepare_images(blocks)
    generate_audio(blocks)
    create_video(blocks)

    print("✅ FINAL VIDEO READY:", FINAL_VIDEO)

if __name__ == "__main__":
    main()