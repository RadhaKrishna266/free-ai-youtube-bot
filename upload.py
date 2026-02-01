import os
import subprocess
from pathlib import Path
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont
import requests
import random

# ====== CONFIG ======
SCRIPT_FILE = "script.txt"  # Your full narration script
TANPURA_FILE = "audio/tanpura.mp3"  # Background tanpura
OUTPUT_VIDEO = "final_video.mp4"
IMAGE_FOLDER = Path("images")
NUM_IMAGES = 10  # Number of images to generate for video scenes
VIDEO_RES = (1280, 720)
NARRATION_FILE = "audio/narration.mp3"

# ====== CREATE FOLDERS ======
IMAGE_FOLDER.mkdir(exist_ok=True)
Path("audio").mkdir(exist_ok=True)

# ====== READ SCRIPT ======
with open(SCRIPT_FILE, encoding="utf-8") as f:
    script_text = f.read().strip()

# ====== GENERATE NARRATION MP3 ======
print("🎙️ Generating narration audio...")
tts = gTTS(script_text, lang='hi')  # Hindi TTS
tts.save(NARRATION_FILE)

# ====== AI IMAGE GENERATION (wallpaper/devotional style) ======
def generate_ai_image(prompt, filename):
    url = f"https://source.unsplash.com/1280x720/?{prompt}"
    r = requests.get(url)
    with open(filename, "wb") as f:
        f.write(r.content)

print("🖼️ Generating images...")
for i in range(NUM_IMAGES):
    prompt = random.choice([
        "Vishnu temple", "Lord Vishnu", "devotional", "Indian mythology",
        "sacred landscape", "Hindu god Vishnu wallpaper"
    ])
    filename = IMAGE_FOLDER / f"{i}.jpg"
    generate_ai_image(prompt, filename)

# ====== CREATE FRONT COVER ======
front_cover = IMAGE_FOLDER / "front.jpg"
img = Image.new("RGB", VIDEO_RES, color=(0, 0, 0))
draw = ImageDraw.Draw(img)
title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
subtitle_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)

draw.text((VIDEO_RES[0]//2, VIDEO_RES[1]//3), "VISHNU PURANA", fill="yellow", anchor="mm", font=title_font)
draw.text((VIDEO_RES[0]//2, VIDEO_RES[1]//2), "Sanatan Gyan Dhara", fill="white", anchor="mm", font=subtitle_font)
img.save(front_cover)

# Add front cover to images
images = [front_cover] + sorted(IMAGE_FOLDER.glob("*.jpg"))
images = [str(img) for img in images if str(img).endswith(".jpg")]

# ====== CREATE VIDEO ======
def run(cmd):
    print("Running:", " ".join(cmd))
    subprocess.run(cmd, check=True)

# Create temporary video segments for each image
temp_videos = []
for idx, img_path in enumerate(images):
    temp_video = IMAGE_FOLDER / f"vid_{idx}.mp4"
    temp_videos.append(str(temp_video))
    duration_cmd = [
        "ffmpeg", "-y", "-loop", "1", "-i", img_path,
        "-c:v", "libx264", "-t", "5", "-pix_fmt", "yuv420p",
        str(temp_video)
    ]
    run(duration_cmd)

# Concatenate all image videos
with open("concat_list.txt", "w") as f:
    for vid in temp_videos:
        f.write(f"file '{vid}'\n")

run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "concat_list.txt",
     "-c:v", "libx264", "-pix_fmt", "yuv420p", "temp_video.mp4"])

# Mix narration + tanpura audio
run([
    "ffmpeg", "-y", "-i", "temp_video.mp4",
    "-i", NARRATION_FILE,
    "-i", TANPURA_FILE,
    "-filter_complex", "[1:a][2:a]amix=inputs=2:duration=first[a]",
    "-map", "0:v", "-map", "[a]",
    "-c:v", "libx264", "-pix_fmt", "yuv420p",
    "-shortest", OUTPUT_VIDEO
])

print(f"✅ Final video ready: {OUTPUT_VIDEO}")