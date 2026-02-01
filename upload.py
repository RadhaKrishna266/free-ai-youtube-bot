import os
import requests
import asyncio
import subprocess
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
import edge_tts

# ---------------- CONFIG ----------------
CHANNEL_NAME = "Sanatan Gyan Dhara"
IMAGE_DIR = "images"
AUDIO_DIR = "audio_blocks"
VIDEO_DIR = "video_blocks"
FINAL_VIDEO = "final_video.mp4"
TANPURA_FILE = "audio/tanpura.mp3"

BLOCKS = 5
WIDTH, HEIGHT = 1280, 720

# ---------------- SETUP ----------------
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs("audio", exist_ok=True)

# ---------------- UTILS ----------------
def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)

def placeholder(path, text="ॐ नमो नारायणाय"):
    img = Image.new("RGB", (WIDTH, HEIGHT), (12, 6, 2))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 56)
    except:
        font = ImageFont.load_default()
    draw.text((80, HEIGHT//2 - 30), text, fill=(255, 215, 0), font=font)
    img.save(path)

# ---------------- AUDIO ----------------
async def tts(text, out):
    voice = "hi-IN-MadhurNeural"
    await edge_tts.Communicate(text, voice).save(out)

def generate_audio_blocks(texts):
    async def runner():
        for i, t in enumerate(texts):
            await tts(t, f"{AUDIO_DIR}/{i:03d}.mp3")
    asyncio.run(runner())

# ---------------- TANPURA ----------------
def generate_tanpura(duration=300):
    if not os.path.exists(TANPURA_FILE):
        run([
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"sine=frequency=110:duration={duration}",
            "-af", "volume=0.15",
            TANPURA_FILE
        ])

# ---------------- IMAGE SOURCE ----------------
def fetch_vishnu_images(count):
    url = "https://www.bhagwanpuja.com/wallpapers/vishnu/"
    images = []

    try:
        html = requests.get(url, timeout=20).text
        soup = BeautifulSoup(html, "lxml")
        tags = soup.find_all("img")

        for tag in tags:
            src = tag.get("src")
            if src and src.startswith("http"):
                images.append(src)

    except Exception as e:
        print("⚠ Wallpaper fetch failed:", e)

    images = list(dict.fromkeys(images))[:count]

    paths = []
    for i, img_url in enumerate(images):
        path = f"{IMAGE_DIR}/{i:03d}.jpg"
        try:
            r = requests.get(img_url, timeout=15)
            if r.status_code == 200:
                with open(path, "wb") as f:
                    f.write(r.content)
            else:
                placeholder(path)
        except:
            placeholder(path)
        paths.append(path)

    # fallback if site fails
    while len(paths) < count:
        p = f"{IMAGE_DIR}/{len(paths):03d}.jpg"
        placeholder(p, "भगवान विष्णु")
        paths.append(p)

    return paths

# ---------------- VIDEO ----------------
def make_block(img, audio, idx):
    out = f"{VIDEO_DIR}/{idx:03d}.mp4"
    run([
        "ffmpeg", "-y",
        "-loop", "1", "-i", img,
        "-i", audio,
        "-i", TANPURA_FILE,
        "-filter_complex",
        "[2:a]volume=0.25[a2];[1:a][a2]amix=inputs=2[a];"
        "[0:v]scale=1280:720:force_original_aspect_ratio=decrease,"
        "pad=1280:720:(ow-iw)/2:(oh-ih)/2,"
        "zoompan=z='min(zoom+0.0006,1.05)':d=150:fps=25[v]",
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-shortest",
        out
    ])
    return out

def concat(clips):
    with open("list.txt", "w") as f:
        for c in clips:
            f.write(f"file '{c}'\n")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "list.txt", "-c", "copy", FINAL_VIDEO])

# ---------------- MAIN ----------------
def main():
    print("🎨 Fetching devotional images...")
    images = fetch_vishnu_images(BLOCKS)

    intro = f"नमस्कार। आप देख रहे हैं {CHANNEL_NAME}। आज हम प्रारंभ कर रहे हैं विष्णु पुराण की दिव्य कथा।"
    middle = "ॐ नमो नारायणाय"
    outro = "यदि यह वीडियो आपको अच्छा लगा हो, तो कृपया लाइक, शेयर और सब्सक्राइब करें। जय श्री हरि।"

    texts = [intro] + [middle]*(BLOCKS-2) + [outro]

    print("🔊 Generating narration...")
    generate_audio_blocks(texts)

    print("🎵 Creating tanpura...")
    generate_tanpura()

    print("🎞 Rendering video blocks...")
    clips = []
    for i in range(BLOCKS):
        clips.append(make_block(images[i], f"{AUDIO_DIR}/{i:03d}.mp3", i))

    print("🔗 Finalizing video...")
    concat(clips)

    print("✅ DONE:", FINAL_VIDEO)

if __name__ == "__main__":
    main()