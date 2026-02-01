import os
import requests
import asyncio
import subprocess
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
import edge_tts

# ================= CONFIG =================
CHANNEL_NAME = "Sanatan Gyan Dhara"
IMAGE_DIR = "images"
AUDIO_DIR = "audio_blocks"
VIDEO_DIR = "video_blocks"
FINAL_VIDEO = "final_video.mp4"
TANPURA_FILE = "audio/tanpura.mp3"
BLOCKS = 5

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
    img = Image.new("RGB", (1280, 720), (15, 10, 5))
    d = ImageDraw.Draw(img)

    try:
        font_big = ImageFont.truetype("DejaVuSans-Bold.ttf", 72)
        font_small = ImageFont.truetype("DejaVuSans.ttf", 42)
    except:
        font_big = font_small = None

    d.text((200, 220), "VISHNU PURANA", fill=(255, 215, 0), font=font_big)
    d.text((260, 330), "Sanatan Gyan Dhara", fill=(255, 255, 255), font=font_small)
    d.text((360, 400), "ॐ नमो नारायणाय", fill=(255, 180, 60), font=font_small)

    img.save(path)
    return path

# ================= IMAGE FETCH =================
def fetch_vishnu_images(count):
    print("🌐 Fetching Vishnu wallpapers...")
    url = "https://www.bhagwanpuja.com/wallpapers/lord-vishnu/"
    images = []

    try:
        r = requests.get(url, timeout=15)
        soup = BeautifulSoup(r.text, "lxml")
        tags = soup.find_all("img")

        for tag in tags:
            src = tag.get("src")
            if not src or "vishnu" not in src.lower():
                continue
            if len(images) >= count:
                break

            path = f"{IMAGE_DIR}/{len(images)+1:03d}.jpg"
            img = requests.get(src, timeout=15)
            if img.status_code == 200:
                with open(path, "wb") as f:
                    f.write(img.content)
                images.append(path)

    except Exception as e:
        print("⚠ Image fetch failed:", e)

    return images

# ================= AUDIO =================
async def tts(text, out):
    t = edge_tts.Communicate(text=text, voice="hi-IN-MadhurNeural")
    await t.save(out)

def generate_audio(texts):
    async def runner():
        for i, t in enumerate(texts):
            await tts(t, f"{AUDIO_DIR}/{i:03d}.mp3")
    asyncio.run(runner())

# ================= TANPURA =================
def generate_tanpura():
    if not os.path.exists(TANPURA_FILE):
        run([
            "ffmpeg", "-y", "-f", "lavfi",
            "-i", "sine=frequency=110:duration=180",
            "-af", "volume=0.15",
            TANPURA_FILE
        ])

# ================= VIDEO BLOCK =================
def make_block(img, audio, idx):
    out = f"{VIDEO_DIR}/{idx:03d}.mp4"
    run([
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", img,
        "-i", audio,
        "-i", TANPURA_FILE,
        "-filter_complex",
        "[2:a]volume=0.25[a2];[1:a][a2]amix=inputs=2:duration=first[a];"
        "[0:v]scale=1280:720:force_original_aspect_ratio=decrease,"
        "pad=1280:720:(ow-iw)/2:(oh-ih)/2[v]",
        "-map", "[v]",
        "-map", "[a]",
        "-t", "8",
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
    print("🚀 Starting Sanatan Gyan Dhara bot")

    images = []
    images.append(create_front_cover())

    others = fetch_vishnu_images(BLOCKS - 1)
    images.extend(others)

    if len(images) < BLOCKS:
        raise Exception("❌ Not enough Vishnu images found")

    texts = [
        f"नमस्कार। आप देख रहे हैं {CHANNEL_NAME}। आज हम Vishnu Purana का प्रथम अध्याय आरंभ करते हैं।"
    ]
    for _ in range(BLOCKS - 2):
        texts.append("ॐ नमो नारायणाय")
    texts.append("इस दिव्य ज्ञान के लिए चैनल को सब्सक्राइब करें। जय श्री हरि।")

    generate_audio(texts)
    generate_tanpura()

    clips = []
    for i in range(BLOCKS):
        clips.append(make_block(images[i], f"{AUDIO_DIR}/{i:03d}.mp3", i))

    concat(clips)
    print("✅ FINAL VIDEO READY:", FINAL_VIDEO)

if __name__ == "__main__":
    main()