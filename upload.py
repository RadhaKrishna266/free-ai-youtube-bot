import os
import subprocess
import requests
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# ================= CONFIG =================
SCRIPT_FILE = "script.txt"
IMAGE_DIR = "images"
VIDEO_DIR = "video"
AUDIO_DIR = "audio"

TANPURA = "audio/tanpura.mp3"
FINAL_VIDEO = "final_video.mp4"

WIDTH, HEIGHT = 1280, 720
SLIDE_DURATION = 8  # seconds per image

os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)

# ================= UTILS =================
def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)

# ================= SCRIPT =================
with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
    blocks = [b.strip() for b in f.read().split("\n\n") if b.strip()]

# ================= IMAGES =================
def generate_ai_image(prompt, out):
    try:
        url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt)}"
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            with open(out, "wb") as f:
                f.write(r.content)
            return True
    except:
        pass
    return False

def placeholder_image(out):
    img = Image.new("RGB", (WIDTH, HEIGHT), (12, 8, 4))
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 60)
    except:
        font = None
    d.text((100, HEIGHT//2 - 40), "ॐ नमो नारायणाय", fill=(255, 215, 0), font=font)
    img.save(out)

print("🖼 Generating Vishnu images...")
for i in range(len(blocks)):
    out = f"{IMAGE_DIR}/{i:03d}.jpg"
    prompt = (
        "Lord Vishnu Vaikuntha divine illustration, "
        "blue skin, golden crown, four arms, conch chakra gada padma, "
        "celestial clouds, spiritual Hindu art, cinematic lighting"
    )
    if not generate_ai_image(prompt, out):
        placeholder_image(out)

# ================= VIDEO SLIDES =================
print("🎞 Creating video slides...")
clips = []

for i in range(len(blocks)):
    img = f"{IMAGE_DIR}/{i:03d}.jpg"
    out = f"{VIDEO_DIR}/{i:03d}.mp4"

    run([
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", img,
        "-t", str(SLIDE_DURATION),
        "-vf", f"scale={WIDTH}:{HEIGHT},format=yuv420p",
        "-c:v", "libx264",
        out
    ])
    clips.append(out)

# ================= CONCAT =================
with open("list.txt", "w") as f:
    for c in clips:
        f.write(f"file '{c}'\n")

run([
    "ffmpeg", "-y",
    "-f", "concat",
    "-safe", "0",
    "-i", "list.txt",
    "-c:v", "copy",
    "silent.mp4"
])

# ================= ADD TANPURA =================
print("🎶 Adding tanpura background...")
run([
    "ffmpeg", "-y",
    "-stream_loop", "-1",
    "-i", TANPURA,
    "-i", "silent.mp4",
    "-shortest",
    "-map", "1:v:0",
    "-map", "0:a:0",
    "-c:v", "copy",
    "-c:a", "aac",
    "-b:a", "128k",
    FINAL_VIDEO
])

print("✅ FINAL VIDEO CREATED:", FINAL_VIDEO)