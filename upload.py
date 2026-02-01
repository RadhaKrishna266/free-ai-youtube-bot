import os
import subprocess
import asyncio
import requests
from PIL import Image, ImageDraw, ImageFont
import edge_tts
import math

# ================= CONFIG =================
CHANNEL_NAME = "Sanatan Gyan Dhara"
IMAGE_DIR = "images"
AUDIO_DIR = "audio_blocks"
VIDEO_DIR = "video_blocks"
FINAL_VIDEO = "final_video.mp4"
TANPURA = "audio/tanpura.mp3"

WIDTH, HEIGHT = 1280, 720
BLOCKS = 8   # More blocks = longer video (safe)

# ================= FOLDERS =================
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs("audio", exist_ok=True)

# ================= UTILS =================
def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)

# ================= FRONT COVER =================
def create_front_cover():
    path = f"{IMAGE_DIR}/000.jpg"
    img = Image.new("RGB", (WIDTH, HEIGHT), (20, 10, 0))
    d = ImageDraw.Draw(img)

    try:
        title_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 72)
        sub_font = ImageFont.truetype("DejaVuSans.ttf", 42)
    except:
        title_font = sub_font = None

    d.rectangle([80, 120, 1200, 600], outline=(255, 215, 0), width=6)
    d.text((300, 260), "VISHNU PURANA", fill=(255, 215, 0), font=title_font)
    d.text((420, 360), CHANNEL_NAME, fill=(255, 230, 180), font=sub_font)
    d.text((460, 430), "ॐ नमो नारायणाय", fill=(255, 200, 120), font=sub_font)

    img.save(path)
    return path

# ================= IMAGE FETCH =================
def fetch_vishnu_images(count):
    urls = [
        "https://wallpapercave.com/wp/wp6957864.jpg",
        "https://wallpapercave.com/wp/wp6957873.jpg",
        "https://wallpapercave.com/wp/wp6957882.jpg",
        "https://wallpapercave.com/wp/wp6957891.jpg",
        "https://wallpapercave.com/wp/wp6957901.jpg",
        "https://wallpapercave.com/wp/wp6957910.jpg",
        "https://wallpapercave.com/wp/wp6957920.jpg",
    ]

    paths = []
    for i in range(1, count + 1):
        path = f"{IMAGE_DIR}/{i:03d}.jpg"
        try:
            r = requests.get(urls[i % len(urls)], timeout=15)
            with open(path, "wb") as f:
                f.write(r.content)
        except:
            create_devotional_placeholder(path)
        paths.append(path)

    return paths

# ================= PLACEHOLDER =================
def create_devotional_placeholder(path):
    img = Image.new("RGB", (WIDTH, HEIGHT), (25, 15, 5))
    d = ImageDraw.Draw(img)
    d.text((420, 340), "ॐ नमो नारायणाय", fill=(255, 215, 0))
    img.save(path)

# ================= AUDIO =================
async def tts(text, out):
    communicate = edge_tts.Communicate(text=text, voice="hi-IN-MadhurNeural")
    await communicate.save(out)

def generate_audio(texts):
    async def runner():
        for i, t in enumerate(texts):
            await tts(t, f"{AUDIO_DIR}/{i:03d}.mp3")
    asyncio.run(runner())

# ================= TANPURA =================
def generate_tanpura(duration):
    if os.path.exists(TANPURA):
        return
    run([
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", f"sine=frequency=110:duration={duration}",
        "-af", "volume=0.15",
        TANPURA
    ])

# ================= VIDEO BLOCK =================
def make_block(img, audio, idx):
    out = f"{VIDEO_DIR}/{idx:03d}.mp4"
    run([
        "ffmpeg", "-y",
        "-loop", "1", "-i", img,
        "-i", audio,
        "-i", TANPURA,
        "-filter_complex",
        "[2:a]volume=0.2[a2];[1:a][a2]amix=inputs=2:duration=first[a];"
        "[0:v]scale=1280:720,zoompan=z='min(zoom+0.0004,1.08)':d=9999:fps=25[v]",
        "-map", "[v]",
        "-map", "[a]",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-shortest",
        out
    ])
    return out

# ================= CONCAT =================
def concat(clips):
    with open("list.txt", "w") as f:
        for c in clips:
            f.write(f"file '{c}'\n")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "list.txt", "-c", "copy", FINAL_VIDEO])

# ================= MAIN =================
def main():
    print("🚀 Starting Sanatan Gyan Dhara")

    images = [create_front_cover()]
    images += fetch_vishnu_images(BLOCKS - 1)

    texts = [
        f"नमस्कार। आप देख रहे हैं {CHANNEL_NAME}। आज हम प्रारंभ कर रहे हैं विष्णु पुराण।"
    ]
    texts += ["ॐ नमो नारायणाय। भगवान विष्णु सम्पूर्ण सृष्टि के पालनकर्ता हैं।"] * (BLOCKS - 2)
    texts += ["इस दिव्य कथा के लिए चैनल को सब्सक्राइब करें। ॐ नमो नारायणाय।"]

    generate_audio(texts)
    generate_tanpura(600)

    clips = []
    for i in range(len(images)):
        clips.append(make_block(images[i], f"{AUDIO_DIR}/{i:03d}.mp3", i))

    concat(clips)
    print("✅ FINAL VIDEO READY")

if __name__ == "__main__":
    main()